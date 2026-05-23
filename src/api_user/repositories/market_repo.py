from typing import Any, Dict, List, Optional

from pymongo import MongoClient


class MarketRepository:
    def __init__(self, client: MongoClient):
        self.collection = client.cryptobot["historical_data_15m"]

    def get_date_range(self) -> tuple[Optional[int], Optional[int]]:
        result = list(
            self.collection.aggregate(
                [
                    {
                        "$group": {
                            "_id": None,
                            "min_time": {"$min": "$open_time"},
                            "max_time": {"$max": "$open_time"},
                        }
                    }
                ]
            )
        )
        if not result:
            return None, None
        return result[0]["min_time"], result[0]["max_time"]

    def get_ohlcv(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query: dict[str, Any] = {}
        if symbol:
            query["symbol"] = symbol.upper()
        time_filter: Dict[str, int] = {}
        if start_time:
            time_filter["$gte"] = start_time
        if end_time:
            time_filter["$lte"] = end_time
        if time_filter:
            query["open_time"] = time_filter

        cursor = self.collection.find(query)
        cursor = cursor.sort("open_time", -1)
        if limit:
            cursor = cursor.limit(limit)
        data = list(cursor)[::-1]
        return data
