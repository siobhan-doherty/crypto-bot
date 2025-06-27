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

    # The data from all trading pairs is stored in a single collection
    # called "historical_data".  Filter by the desired pair via the
    # `symbol` field (added when the data was ingested).
    collection_name = "historical_data"
    collection = db[collection_name]

    query = {"symbol": trading_pair} if trading_pair else {}

    print(f"Querying collection '{collection_name}' with filter: {query}")
    data = list(collection.find(query))
    df = pd.DataFrame(data) if data else pd.DataFrame()

    if df.empty:
        print("No matching documents found.")
        return df

    # Convert timestamps and add helper / renamed columns if needed
    if "close_time" in df.columns:
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")

    # Ensure a uniform column identifying the trading pair
    if "symbol" in df.columns:
        df.rename(columns={"symbol": "trading_pair"}, inplace=True)
    df["trading_pair"] = df.get("trading_pair", trading_pair)

    print(f"Fetched {len(df)} records for {trading_pair if trading_pair else 'all pairs'} from '{collection_name}'.")
    return df