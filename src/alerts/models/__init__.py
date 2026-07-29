from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PriceAlert:
    symbol: str          # BTC/USDT
    exchange: str        # e.g. binance, kraken
    threshold: float     # price level in quote currency
    condition: str       # 'above' or 'below'
    last_triggered_price: Optional[float] = None    # to avoid duplicate alerts
    last_alert_time: Optional[datetime] = None
    fallback_exchanges: Optional[list[str]] = None
