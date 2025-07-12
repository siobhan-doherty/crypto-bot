from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pymongo import MongoClient
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import pandas as pd
import asyncio

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

def get_clean_dataframe(
    collection,
    minutes: int = 60,  # Default to 60 minutes of data
    sort_field: str = "ts",
    projection: dict = {"_id": 0, "ts": 1, Y_VALUE: 1},
    filters: dict = {}
) -> pd.DataFrame:
    """
    Query MongoDB for data within a specific time window, clean the result, and return a Pandas DataFrame.

    :param minutes: Number of minutes of historical data to retrieve
    :param sort_field: Field to sort by (default: "ts")
    :param projection: Fields to include in the result
    :param filters: Additional MongoDB query filters
    :return: Cleaned Pandas DataFrame with 'ts' and the specified Y_VALUE column
    """
    try:
        # Ensure we're getting the required fields
        required_fields = {"ts": 1, Y_VALUE: 1}
        for field in required_fields:
            if field not in projection:
                projection[field] = required_fields[field]
        
        # Calculate the timestamp for X minutes ago
        from datetime import datetime, timedelta, timezone
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        # Add time filter to existing filters
        time_filter = {"ts": {"$gte": time_threshold.isoformat()}}
        query = {**filters, **time_filter}
        
        # Query MongoDB with the time filter and projection
        logger.debug(f"Querying MongoDB with filter: {query}")
        cursor = collection.find(query, projection).sort(sort_field, -1)
        
        # Convert cursor to list and then to DataFrame
        records = list(cursor)
        logger.debug(f"Retrieved {len(records)} records from MongoDB")
        
        if not records:
            logger.warning("No records found in the query results")
            return pd.DataFrame(columns=["ts", Y_VALUE])
            
        df = pd.DataFrame(records)
        logger.debug(f"Original DataFrame columns: {df.columns.tolist()}")
        
        if "ts" not in df.columns:
            logger.warning("'ts' column not found in query results. Using current time.")
            df["ts"] = pd.Timestamp.now()
        
        if Y_VALUE not in df.columns:
            logger.warning(f"'{Y_VALUE}' column not found in query results. Using 0 as default.")
            df[Y_VALUE] = 0.0
        
        # Ensure ts is datetime and Y_VALUE is float
        df["ts"] = pd.to_datetime(df["ts"])
        df[Y_VALUE] = pd.to_numeric(df[Y_VALUE], errors='coerce')
        
        # Log any null values that were converted to NaN
        null_values = df[Y_VALUE].isna().sum()
        if null_values > 0:
            logger.warning(f"Found {null_values} null/NaN values in {Y_VALUE} column")
        
        # Fill NaN values with 0.0 after logging
        df[Y_VALUE] = df[Y_VALUE].fillna(0.0)
        
        # Sort by timestamp and ensure we're within the time window
        df = df[df["ts"] >= time_threshold]
        df = df.sort_values("ts").reset_index(drop=True)
        
        # Log the time range of the data
        if not df.empty:
            logger.debug(f"Data time range: {df['ts'].min()} to {df['ts'].max()}")
            logger.debug(f"Value range for {Y_VALUE}: {df[Y_VALUE].min()} to {df[Y_VALUE].max()}")
        
        # Keep only the required columns to be safe
        df = df[["ts", Y_VALUE]]
        
        return df

    except Exception as e:
        logger.error(f"Error in get_clean_dataframe: {str(e)}")
        # Return empty DataFrame with expected columns on error
        return pd.DataFrame(columns=["ts", "value"])

def convert_timestamps(record):
    """Convert any timestamp fields in the record to ISO format strings."""
    if isinstance(record, dict):
        return {k: v.isoformat() if hasattr(v, 'isoformat') else v 
                for k, v in record.items()}
    return record

@router.websocket("/ws/stream/{symbol}")
async def stream_data(websocket: WebSocket, symbol: str):
    await websocket.accept()
    try:
        # Convert symbol to uppercase to match the format in the database
        symbol = symbol.upper()
        logger.info(f"New WebSocket connection for symbol: {symbol}")
        
        async with get_mongodb_connection() as collection:
            while True:
                try:
                    # Get the data from MongoDB for the specified symbol (last 60 minutes by default)
                    df = get_clean_dataframe(
                        collection, 
                        minutes=60,
                        filters={"symbol": symbol}
                    )

                    data = []
                    for record in df.to_dict(orient="records"):
                        # Convert any timestamp fields to ISO format strings
                        processed_record = convert_timestamps(record)
                        data.append(processed_record)
                    
    
                    await websocket.send_json({
                        "symbol": symbol,
                        "data": data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await asyncio.sleep(20)  # adjustable streaming interval
                    
                except Exception as e:
                    error_msg = f"Error fetching data for {symbol}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await websocket.send_json({
                        "error": error_msg,
                        "symbol": symbol,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    break
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        error_msg = f"WebSocket error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)