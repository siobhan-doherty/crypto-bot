from pymongo import MongoClient
import pandas as pd
import os

MONGO_URI = os.getenv('MONGO_URI')

def get_mongo_client():
    print("Attempting to connect to MongoDB...")
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

def fetch_historical_data(trading_pair="BTCUSDT"):
    """
    Fetch historical data for a specific trading pair.
    
    Args:
        trading_pair (str): The trading pair to fetch data for (e.g., 'BTCUSDT', 'ETHUSDT', 'ETHBTC')
        
    Returns:
        pd.DataFrame: DataFrame containing the historical data
    """
    print(f"Fetching historical data for {trading_pair}...")
    client = get_mongo_client()
    print("Connected to MongoDB")
    db = client["cryptobot"]
    
    collections = db.list_collection_names()
    print("\nAvailable collections:")
    for col in collections:
        print(f"- {col}")
    
    collection_name = f"historical_data_{trading_pair}_4h"
    print(f"\nTrying to access collection: {collection_name}")
    
    if collection_name in collections:
        collection = db[collection_name]
        data = list(collection.find())
        df = pd.DataFrame(data) if data else pd.DataFrame()
        
        if not df.empty:
            if 'close_time' in df.columns:
                df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            df['trading_pair'] = trading_pair
            print(f"Successfully fetched {len(df)} records for {trading_pair}")
            return df
        else:
            print(f"\nWarning: Collection '{collection_name}' is empty")
            return pd.DataFrame()
    else:
        print(f"\nError: Collection '{collection_name}' not found")
        print("Available collections:", ", ".join(collections))
        return pd.DataFrame()