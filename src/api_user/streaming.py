from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
import os
import json
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

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

@router.websocket("/ws/stream")
async def stream_data(websocket: WebSocket):
    await websocket.accept()
    try:
        async with get_mongodb_connection() as collection:
            while True:
                try:
                    latest = collection.find().sort("timestamp", -1).limit(1)
                    # Convert MongoDB documents to JSON-serializable format
                    data = []
                    for doc in latest:
                        doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                        data.append(doc)
                    
                    await websocket.send_text(dumps(data))  # Use bson.json_util.dumps
                    await asyncio.sleep(2)  # adjustable streaming interval
                except Exception as e:
                    logger.error(f"Error fetching data: {str(e)}")
                    await websocket.send_text(dumps({"error": str(e)}))
                    break
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))