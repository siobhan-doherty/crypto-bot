from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PriceAlert:
    symbol: str          # BTC/USDT
    threshold: float     # price level in USDT
    condition: str       # 'above' or 'below'
    last_triggered_price: Optional[float] = None  # to avoid duplicate alerts
    last_alert_time: Optional[datetime] = None
