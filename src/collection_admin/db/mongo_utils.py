import logging
from pymongo import MongoClient
from api_user.config import settings

logger = logging.getLogger(__name__)


def get_mongo_collection(db_name: str, collection_name: str):
    """Returns MongoDB collection."""
    try:
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client[db_name][collection_name]

    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        raise RuntimeError(f"MongoDB connection error: {e}") from e


def save_to_collection(db_name: str, collection_name: str, data: dict):
    """Inserts a document into MongoDB."""
    collection = get_mongo_collection(db_name, collection_name)
    result = collection.insert_one(data)
    logger.info(f"Inserted _id = {result.inserted_id} into {db_name}.{collection_name}")
