from pymongo import MongoClient
from api_user.config import settings


def get_mongo_client() -> MongoClient:
    """Return Mongodb client. raises ValueError if MONGO_URI is not set."""
    if not settings.MONGO_URI:
        raise ValueError("MONGO_URI is not set")
    
    return MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS = 5000)
