import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.pattern_analytics.feature_extractor import FeatureExtractor
from src.pattern_analytics.embedder import PatternEmbedder
from src.pattern_analytics.clusterer import PatternClusterer

logging.basicConfig(level=logging.INFO)


def load_historical_data():
    """
    load real OHLCV data from MongoDB, returns a DataFrame with columns: timestamp, open, high, low, close, volume.
    """
    from pymongo import MongoClient
    import pandas as pd

    client = MongoClient("mongodb://localhost:27017")
    db = client["cryptobot"]
    collection = db["streaming_data_1m"]
    # fetch last 10000 documents for BTC/USDT
    cursor = collection.find(
        {"symbol": "BTC/USDT"},
        {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "timestamp": 1, "open_time": 1}
    ).sort("timestamp", -1).limit(10000)

    df = pd.DataFrame(list(cursor))
    if df.empty:
        raise ValueError("No data found in MongoDB")
    # normalise column names
    # handle common variations if 'timestamp' doesn't exist, try 'open_time' or '_id'
    if "timestamp" not in df.columns:
        if "open_time" in df.columns:
            df.rename(columns = {"open_time": "timestamp"}, inplace = True)
        elif "_id" in df.columns:
            # Convert ObjectId to datetime
            df["timestamp"] = df["_id"].apply(lambda x: x.generation_time if hasattr(x, "generation_time") else None)
        else:
            raise KeyError("No timestamp column found in MongoDB documents")
    # ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit = "ms", errors = "coerce")
    # drop rows with null timestamp
    df = df.dropna(subset = ["timestamp"])
    # sort by timestamp
    df = df.sort_values("timestamp")
    # keep only required columns
    required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    df = df[required_cols].copy()
    logger.info(f"Loaded {len(df)} rows from MongoDB")
    return df


def main():
    logger = logging.getLogger(__name__)
    # load historical data
    df = load_historical_data()
    logger.info(f"Loaded {len(df)} rows")
    window_size = 30
    feature_vectors = []
    timestamps = []

    for i in range(window_size, len(df)):
        window = df.iloc[i - window_size:i]
        features = FeatureExtractor.extract_features(window)
        if features:
            feature_vectors.append(list(features.values()))
            timestamps.append(df.iloc[i]["timestamp"])

    feature_vectors = np.array(feature_vectors)
    logger.info(f"Extracted {len(feature_vectors)} feature vectors")
    # fit embedder
    embedder = PatternEmbedder(embedding_dim = 8)
    embedder.fit(feature_vectors)
    embeddings = embedder.embed_batch(feature_vectors)
    # fit clusterer
    clusterer = PatternClusterer(min_cluster_size = 20)
    cluster_labels = clusterer.fit(embeddings)
    # train K‑means for fast prediction
    try:
        clusterer.fit_kmeans_from_hdbscan(embeddings)
    except Exception as e:
        logger.warning(f"K‑means training failed, continuing with HDBSCAN only: {e}")
    # log results
    n_clusters = len(set(cluster_labels) - {-1})
    logger.info(f"Training complete: {n_clusters} clusters found")
    logger.info(f"Cluster distribution: {np.bincount(cluster_labels[cluster_labels != -1])}")


if __name__ == "__main__":
    main()
