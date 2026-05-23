from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from api_user.repositories.market_repo import MarketRepository


class MarketService:
    def __init__(self, repo: MarketRepository):
        self.repo = repo

    def get_date_range(self) -> dict[str, str]:
        min_time, max_time = self.repo.get_date_range()
        if min_time is None or max_time is None:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days = 7)
            return {
                "min_date": start_date.isoformat(),
                "max_date": end_date.isoformat(),
            }
        assert min_time is not None and max_time is not None
        min_date = datetime.fromtimestamp(min_time / 1000, tz = timezone.utc)
        max_date = datetime.fromtimestamp(max_time / 1000, tz = timezone.utc)
        return {"min_date": min_date.isoformat(), "max_date": max_date.isoformat()}

    def get_ohlcv(
        self,
        symbol: Optional[str] = None,
        interval: str = "15m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        data = self.repo.get_ohlcv(symbol, start_time, end_time, limit)
        # convert to api response format
        return [
            {
                "_id": str(doc["_id"]),
                "symbol": doc["symbol"],
                "open_datetime": datetime.fromtimestamp(
                    doc["open_time"] / 1000, tz=timezone.utc
                ).isoformat(),
                "close_datetime": datetime.fromtimestamp(
                    doc["close_time"] / 1000, tz=timezone.utc
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
            }
            for doc in data
        ]
