from pydantic import BaseModel
from datetime import datetime


class OHLCVDataPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    interval: str
