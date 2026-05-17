from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, Any
from datetime import datetime, timedelta, timezone
from src.api_user.database.mongo import get_mongo_client

COLLECTION = "historical_data_15m"
router = APIRouter()


@router.get("/market/range")
async def get_date_range() -> dict[str, str]:
    client = None
    try:
        client = get_mongo_client()
        db = client.cryptobot

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
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days = 7)
            return {
                "min_date": start_date.isoformat(),
                "max_date": end_date.isoformat(),
            }

        min_date = datetime.fromtimestamp(
            result[0]["min_time"] / 1000, tz = timezone.utc
        )
        max_date = datetime.fromtimestamp(
            result[0]["max_time"] / 1000, tz = timezone.utc
        )
        return {
            "min_date": min_date.isoformat(), 
            "max_date": max_date.isoformat()
        }
    finally:
        if client is not None:
            client.close()


@router.get("/market/ohlcv")
async def get_ohlcv(
    symbol: Optional[str] = Query(default = None),
    interval: str = Query(default = "15m"),
    start_time: Optional[int] = Query(default = None),
    end_time: Optional[int] = Query(default = None),
    limit: Optional[int] = Query(default = None, ge = 1),
):
    client = None
    try:
        client = get_mongo_client()
        collection = client.cryptobot[COLLECTION]
        query = {}

        if symbol:
            query["symbol"] = symbol.upper()
        time_query = {}
        if start_time is not None:
            time_query["$gte"] = start_time
        if end_time is not None:
            time_query["$lte"] = end_time
        if time_query:
            query["open_time"] = time_query

        cursor = collection.find(query)
        if limit:
            data = list(cursor.sort("open_time", -1).limit(limit))[::-1] 
        else: 
            data = list(cursor.sort("open_time", 1))

        return [{
            "_id": str(doc["_id"]),
            "symbol": doc["symbol"],
            "open_datetime": datetime.fromtimestamp(
                doc["open_time"] / 1000, tz = timezone.utc
            ).isoformat(),
            "close_datetime": datetime.fromtimestamp(
                doc["close_time"] / 1000, tz = timezone.utc
            ).isoformat(),
            "open": doc["open"],
            "high": doc["high"],
            "low": doc["low"],
            "close": doc["close"],
            "volume": doc["volume"],
            "quote_volume": doc.get("quote_volume"),
            "num_trades": doc.get("num_trades"),
            "taker_base_volume": doc.get("taker_base_volume"),
            "taker_quote_volume": doc.get("taker_quote_volume"),
            "interval": interval,
        } for doc in data]
    finally:
        if client is not None:
            client.close()
