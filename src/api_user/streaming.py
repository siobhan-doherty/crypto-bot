import asyncio
import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pymongo import MongoClient
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pymongo.collection import Collection
from api_user.config import settings

router = APIRouter()

# configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

DB_NAME = "cryptobot"
COLLECTION_NAME = "streaming_data_1m"
Y_VALUE = "close"


@asynccontextmanager
async def get_mongodb_connection():
    client = None
    try:
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.debug("Connected to MongoDB")
        yield client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if client:
            client.close()


def fetch_data(collection: Collection, minutes: int = 60, filters: dict = None) -> list:
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
                "$lte": end_time.isoformat(),
            }
        }
        query = {**filters, **time_filter}
        cursor = collection.find(
            query, projection={"_id": 0, "close_datetime": 1, "close": 1}
        )
        return list(cursor)
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return []


@router.websocket("/ws/stream")
async def stream_data(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket connection")
    # first message to confirm connection
    await websocket.send_json(
        {"status": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    try:
        async with get_mongodb_connection() as collection:
            while True:
                try:
                    for symbol in ["BTCUSDT", "ETHUSDT"]:
                        records = fetch_data(
                            collection, minutes=60, filters={"symbol": symbol}
                        )
                        formatted_records = []
                        for record in records:
                            # get timestamp value
                            ts = record.get(
                                "close_datetime", datetime.now(timezone.utc)
                            )
                            # convert to ISO format if it's a datetime object
                            if isinstance(ts, datetime):
                                ts = ts.isoformat()
                            formatted_records.append(
                                {
                                    "symbol": record.get("symbol", symbol),
                                    "close": record.get("close"),
                                    "close_datetime": ts,
                                }
                            )
                        if formatted_records:
                            await websocket.send_json(
                                {
                                    "data": formatted_records,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                    # add small delay to prevent overwhelming the client
                    await asyncio.sleep(30)
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error in stream loop: {e}")
                    await asyncio.sleep(5)  # wait before retrying

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close()
