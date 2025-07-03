import os
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from typing import Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

class OHLCVDataPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    interval: str

COLLECTION = 'historical_data_15m'
router = APIRouter()

def get_mongo_client():
    try:
        mongo_uri = os.getenv("MONGO_URI")
        print(f"[DEBUG] Connecting to MongoDB at: {mongo_uri}")
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        client.server_info()
        print("[DEBUG] Successfully connected to MongoDB")
        return client
    except Exception as e:
        error_msg = f"MongoDB connection error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/test")
async def test_endpoint():
    return {"status": "API is working!"}

@router.get("/market/inspect_data")
async def inspect_all_data(sample_size: int = 3):
    """Get complete data inspection including symbols, date ranges, and sample documents"""
    client = get_mongo_client()
    try:
        db = client["cryptobot"]
        collection = db["historical_data"]
        
        total_docs = collection.count_documents({})
        symbols = collection.distinct("symbol")
        intervals = collection.distinct("interval")
        
        # Get overall date range
        first_doc = collection.find_one(sort=[("open_datetime", 1)])
        last_doc = collection.find_one(sort=[("open_datetime", -1)])
        
        # Get sample documents (one per symbol)
        sample_docs = {}
        for symbol in symbols:
            sample = collection.find_one({"symbol": symbol})
            if sample and "_id" in sample:
                sample["_id"] = str(sample["_id"])
                sample_docs[symbol] = sample
        
        # Get date ranges per symbol
        symbol_stats = {}
        for symbol in symbols:
            first = collection.find_one({"symbol": symbol}, sort=[("open_datetime", 1)])
            last = collection.find_one({"symbol": symbol}, sort=[("open_datetime", -1)])
            count = collection.count_documents({"symbol": symbol})
            dt1 = datetime.fromisoformat(first["open_datetime"].replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(first["close_datetime"].replace('Z', '+00:00'))
            
            symbol_stats[symbol] = {
                "data_points": count,
                "date_range": {
                    "from": dt1,
                    "to": dt2
                },
                "interval in seconds": (dt2 - dt1) if first else None
            }
        
        return {
            "collection": COLLECTION,
            "total_documents": total_docs,
            "all_symbols": symbols,
            "all_intervals": intervals, 
            "overall_date_range": {
                "from": first_doc.get("open_datetime") if first_doc else None,
                "to": last_doc.get("open_datetime") if last_doc else None
            },
            "symbol_stats": symbol_stats,
            "sample_documents": sample_docs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inspecting data: {str(e)}")
    finally:
        client.close()

@router.get("/market/range")
async def get_date_range():
    """
    Get the complete available date range from the database.
    This endpoint is not affected by any limit parameters.
    
    Returns:
        dict: Dictionary with min_date and max_date in ISO format
    """
    client = None
    try:
        client = get_mongo_client()
        db = client.cryptobot
        
        # Use aggregation to get min and max in a single query
        result = list(db[COLLECTION].aggregate([
            {
                "$group": {
                    "_id": None,
                    "min_time": {"$min": "$open_time"},
                    "max_time": {"$max": "$open_time"}
                }
            }
        ]))
        
        if not result:
            raise ValueError("No data found in the collection")
        
        if not result:
            # Default to last 7 days if no data is found
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            return {
                'min_date': start_date.isoformat(),
                'max_date': end_date.isoformat()
            }
            
        # Get the min and max timestamps from the aggregation result
        min_time = result[0]['min_time']
        max_time = result[0]['max_time']
        
        # Convert timestamps to datetime objects
        min_date = datetime.fromtimestamp(min_time / 1000, tz=timezone.utc)
        max_date = datetime.fromtimestamp(max_time / 1000, tz=timezone.utc)
            
        return {
            'min_date': min_date.isoformat(),
            'max_date': max_date.isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching date range from database: {e}")
        # Fallback to default range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        return {
            'min_date': start_date.isoformat(),
            'max_date': end_date.isoformat(),
            'error': str(e)
        }
    finally:
        if client:
            client.close()


@router.get("/market/ohlcv")
async def get_ohlcv(
    symbol: str,
    interval: str = "15m",
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: Optional[int] = None
):
    """
    Get OHLCV data for a specific symbol and time range.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        interval: Candle interval (e.g., '1d', '1h')
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch
        limit: Optional maximum number of candles to return. If not specified, returns all matching records.
        
    Returns:
        List of OHLCV data points with datetime strings
    """
    client = None
    try:
        client = get_mongo_client()
        db = client.cryptobot
        collection = db[COLLECTION]
        
        query = {"symbol": symbol.upper()}
        
        # Convert timestamp range to milliseconds for query
        time_query = {}
        if start_time is not None:
            time_query["$gte"] = start_time
        if end_time is not None:
            time_query["$lte"] = end_time
            
        if time_query:
            query["open_time"] = time_query
        
        # If limit is specified, get the most recent data by sorting in descending order
        if limit is not None and limit > 0:
            cursor = collection.find(query).sort("open_time", -1).limit(limit)
            # Convert to list and reverse to maintain chronological order
            data = list(cursor)[::-1]
        else:
            # No limit, get all data in chronological order
            cursor = collection.find(query).sort("open_time", 1)
            data = list(cursor)
            
        if not data:
            return []
            
        results = []
        for doc in data:
            # Convert timestamps to ISO format
            open_time = datetime.fromtimestamp(doc['open_time'] / 1000, tz=timezone.utc).isoformat()
            close_time = datetime.fromtimestamp(doc['close_time'] / 1000, tz=timezone.utc).isoformat()
            
            result = {
                '_id': str(doc['_id']),
                'symbol': doc['symbol'],
                'open_datetime': open_time,
                'close_datetime': close_time,
                'open': doc['open'],
                'high': doc['high'],
                'low': doc['low'],
                'close': doc['close'],
                'volume': doc['volume'],
                'quote_volume': doc.get('quote_volume'),
                'num_trades': doc.get('num_trades'),
                'taker_base_volume': doc.get('taker_base_volume'),
                'taker_quote_volume': doc.get('taker_quote_volume'),
                'interval': interval
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"Error in get_ohlcv: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if client:
            client.close()