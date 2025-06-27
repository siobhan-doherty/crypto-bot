import os
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from typing import List, Optional, Dict, Any
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
            "collection": "historical_data",
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
    Get the available date range from the database.
    
    Returns:
        dict: Dictionary with min_date and max_date in ISO format
    """
    client = None
    try:
        client = get_mongo_client()
        db = client.cryptobot
        
        # Get the first and last record
        first = db.historical_data.find_one(sort=[('open_time', 1)])
        last = db.historical_data.find_one(sort=[('open_time', -1)])
        
        if not first or not last:
            # Default to last 7 days if no data is found
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            return {
                'min_date': start_date.isoformat(),
                'max_date': end_date.isoformat()
            }
        
        # Convert timestamps to datetime objects
        min_date = datetime.fromtimestamp(first['open_time'] / 1000, tz=timezone.utc)
        max_date = datetime.fromtimestamp(last['open_time'] / 1000, tz=timezone.utc)
            
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

# TODO remove debug output
@router.get("/market/ohlcv")
async def get_ohlcv(
    symbol: str,
    interval: str = "1d",
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 1000
):
    """
    Get OHLCV data for a specific symbol and time range.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        interval: Candle interval (e.g., '1d', '1h')
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch
        limit: Maximum number of candles to return
        
    Returns:
        List of OHLCV data points with datetime strings
    """
    client = None
    try:
        client = get_mongo_client()
        db = client.cryptobot
        collection = db.historical_data
        
        # Build query
        query = {"symbol": symbol.upper()}
        
        # Add time range to query if provided
        if start_time is not None or end_time is not None:
            time_query = {}
            if start_time is not None:
                start_dt = datetime.fromtimestamp(start_time/1000, tz=timezone.utc).isoformat()
                time_query["$gte"] = start_dt
                print(f"[DEBUG] Start datetime: {start_dt}")
            if end_time is not None:
                end_dt = datetime.fromtimestamp(end_time/1000, tz=timezone.utc).isoformat()
                time_query["$lte"] = end_dt
                print(f"[DEBUG] End datetime: {end_dt}")
            query["open_datetime"] = time_query
        
        print(f"[DEBUG] Executing query: {query}")
        
        cursor = collection.find(query).sort("open_datetime", 1).limit(limit)
        
        # Convert cursor to list of documents
        data = list(cursor)
        print(f"[DEBUG] Found {len(data)} documents")
        
        if not data:
            print("[WARNING] No data found for the given query")
            return []
            
        # Format the response
        results = []
        for doc in data:
            result = {
                '_id': str(doc['_id']),
                'open_datetime': doc.get('open_datetime'),
                'close_datetime': doc.get('close_datetime'),
                'open': doc.get('open'),
                'high': doc.get('high'),
                'low': doc.get('low'),
                'close': doc.get('close'),
                'volume': doc.get('volume'),
                'symbol': doc.get('symbol', symbol.upper()),
                'interval': doc.get('interval', interval)
            }
            results.append(result)
        
        print(f"Returning {len(results)} OHLCV records for {symbol}")
        return results
        
    except Exception as e:
        error_msg = f"Error in get_ohlcv: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(
            status_code=500, 
            detail=error_msg
        )
    finally:
        if 'client' in locals():
            client.close()