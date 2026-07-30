from pymongo import MongoClient
from api_user.config import settings


class MongoDB:
    """MongoDB connection manager."""
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(uri, serverSelectionTimeoutMS = 5000)


    def get_collection(self, db_name: str, collection_name: str):
        """Get a MongoDB collection."""
        return self.client[db_name][collection_name]


def get_mongo_client() -> MongoClient:
    """Return Mongodb client. raises ValueError if MONGO_URI is not set."""
    if not settings.MONGO_URI:
        raise ValueError("MONGO_URI is not set")

    return MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS = 5000)
