from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pymongo import MongoClient
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import asyncio
from pymongo.collection import Collection

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection configuration
MONGODB_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://localhost:27017/cryptobot?authSource=admin"
)
MONGODB_USERNAME = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "admin")
MONGODB_PASSWORD = os.environ.get("MONGO_INITDB_ROOT_PASSWORD", "admin")
DB_NAME = "cryptobot"
COLLECTION_NAME = "streaming_data_1m"
Y_VALUE = "close"

@asynccontextmanager
async def get_mongodb_connection():
    try:
        mongo_uri = os.getenv("MONGO_URI")
        print(f"[DEBUG] Connecting to MongoDB at: {mongo_uri}")

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Test the connection
        try:
            client.server_info()
            print("[DEBUG] Successfully connected to MongoDB")
        except Exception as e:
            error_msg = f"MongoDB connection error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        yield collection
    except Exception as e:
        error_msg = f"MongoDB connection error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        client.close()

def fetch_data(
    collection: Collection,
    minutes: int = 60,
    filters: dict = None
) -> list:
    """
    Fetch recent data from MongoDB collection.
    
    Args:
        collection: MongoDB collection to query
        minutes: Number of minutes of data to retrieve
        filters: Additional MongoDB query filters
        
    Returns:
        List of records with close_datetime and close values
    """
    if filters is None:
        filters = {}
    
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes)
        
        time_filter = {
            "close_datetime": {
                "$gte": start_time.isoformat(),
                "$lte": end_time.isoformat()
            }
        }
        
        query = {**filters, **time_filter}
        cursor = collection.find(
            query,
            projection={"_id": 0, "close_datetime": 1, "close": 1}
        )
        
        return list(cursor)
        
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return []

def convert_timestamps(record):
    """Convert timestamp fields to ISO format strings."""
    if isinstance(record, dict):
        # Convert only the timestamp field, leave close_time as datetime
        return {
            k: v.isoformat() if k == 'timestamp' and hasattr(v, 'isoformat') else v
            for k, v in record.items()
        }
    return record

@router.websocket("/ws/stream")
async def stream_data(websocket: WebSocket):
    await websocket.accept()
    try:
        logger.info(f"New WebSocket connection")
        
        # First message to confirm connection
        await websocket.send_json({
            "status": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        async with get_mongodb_connection() as collection:
            while True:
                try:
                    for symbol in ["BTCUSDT", "ETHUSDT"]:
                        records = fetch_data(
                            collection,
                            minutes=60,
                            filters={"symbol": symbol}
                        )
                        formatted_records = []
                        for record in records:
                            try:
                                # Get the timestamp value
                                timestamp = record.get('close_datetime', datetime.now(timezone.utc))
                                # Convert to ISO format if it's a datetime object
                                if isinstance(timestamp, datetime):
                                    timestamp = timestamp.isoformat()
                                
                                formatted_record = {
                                    'symbol': record.get('symbol', symbol),
                                    'close': record.get('close'),
                                    'close_datetime': timestamp
                                }
                                formatted_records.append(formatted_record)
                            except Exception as e:
                                logger.error(f"Error formatting record: {str(e)}")
                                continue

                        if formatted_records:
                            await websocket.send_json({
                                "data": formatted_records,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })

                        # Add a small delay to prevent overwhelming the client
                        await asyncio.sleep(30)

                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error in stream loop: {str(e)}")
                    await asyncio.sleep(5)  # Wait before retrying

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        await websocket.close()
        raise
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        error_msg = f"WebSocket error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)