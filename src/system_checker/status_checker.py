import os
from pymongo import MongoClient
from dotenv import load_dotenv
import requests
import sys

load_dotenv()

def check_mongo():
    # Check MongoDB connection and collections
    print("Checking MongoDB connection and collections...")
    try:
        if "MONGO_URI" not in os.environ:
            print(" MongoDB URI not set in environment variables.")
            sys.exit(1)
        if not os.getenv("MONGO_URI"):
            print(" MongoDB URI is empty.")
            sys.exit(1)
        
        # Connect to MongoDB
        print(" Connecting to MongoDB...")
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client["cryptobot"]
        collections = db.list_collection_names()

        if "historical_data" in collections:
            print(" MongoDB OK - 'historical_data' collection found.")        
        else:
            print(" MongoDB connected, but 'historical_data' collection missing.")

        if "streaming_data" in collections:
            print(" MongoDB OK - 'streaming_data' collection found.")
        else:
            print(" MongoDB connected, but 'streaming_data' collection missing.")
        
        client.close()
        print(" MongoDB connection closed.")

    except Exception as e:
        print(f" MongoDB connection failed: {e}")
        sys.exit(1)
    
def check_dash():
    try:
        response = requests.get("http://crypto_dash:8050")
        if response.status_code == 200:
            return {"dash": "Dashboard is running"}
        else:
            print(" Dash not responding, status code:", response.status_code)
    except Exception as e:
        print(f" Dash connection failed: {e}")

# Main execution
if __name__ == "__main__":
    print("Starting system checks...")
    check_mongo()
    check_dash()