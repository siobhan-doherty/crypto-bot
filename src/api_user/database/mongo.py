import os
from pymongo import MongoClient


def get_mongo_client() -> MongoClient:
    """Return Mongodb client. raises ValueError if MONGO_URI is not set."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI is not set")
    
    return MongoClient(mongo_uri, serverSelectionTimeoutMS = 5000)
