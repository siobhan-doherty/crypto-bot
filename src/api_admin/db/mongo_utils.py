from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_mongo_collection(db_name: str, collection_name: str):
    """
    Connects to MongoDB and returns the specified collection.
    """
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI not set in environment variables.")
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    return db[collection_name]


def save_to_collection(db_name: str, collection_name: str, data: dict):
    """
    Inserts a document into the specified MongoDB collection.
    """
    try:
        collection = get_mongo_collection(db_name, collection_name)
        result = collection.insert_one(data)
        print(f"Document inserted with _id: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting into MongoDB: {e}")
