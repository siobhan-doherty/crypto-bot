from pymongo import MongoClient
from dotenv import load_dotenv
import os


# load ROOT environment
load_dotenv(dotenv_path = "/app/.env", override = True)

def get_mongo_collection(db_name: str, collection_name: str):
    """Connects to MongoDB and returns the specified collection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI not set in environment variables.")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS = 5000)
        client.admin.command("ping")
        return client[db_name][collection_name]
    except Exception as e:
        print(f"Unexpected error while connecting to MongoDB: {e}")
        raise

def save_to_collection(db_name: str, collection_name: str, data: dict):
    """Inserts a document into the specified MongoDB collection."""
    try:
        collection = get_mongo_collection(db_name, collection_name)
        result = collection.insert_one(data)
        print(f"Inserted _id = {result.inserted_id} into {db_name}.{collection_name}")
    except Exception as e:
        print(f"Error inserting into MongoDB: {e}")

