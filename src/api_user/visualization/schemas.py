from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, model_validator


class KlineData(BaseModel):
    """Model for single cryptocurrency kline/candlestick data point"""

    symbol: str = Field(..., description="Trading pair symbol, e.g. BTCUSDT")
    close: float = Field(..., description="Closing price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    open: float = Field(..., description="Opening price")
    volume: float = Field(..., description="Base asset volume")
    close_time: int = Field(..., description="Close timestamp in milliseconds")
    quote_volume: float = Field(..., description="Quote asset volume")
    num_trades: int = Field(..., description="Number of trades")
    taker_base_volume: float = Field(..., description="Taker buy base asset volume")
    taker_quote_volume: float = Field(..., description="Taker buy quote asset volume")
    open_datetime: datetime = Field(..., description="ISO formatted open datetime")
    close_datetime: datetime = Field(..., description="ISO formatted close datetime")
    price_change: float = Field(..., description="Change between close and open prices")
    price_change_pct: float = Field(..., description="Percentage price change")
    high_low_spread: float = Field(..., description="Difference between high and low")
    high_low_spread_pct: float = Field(..., description="Percentage spread")
    ts: datetime = Field(..., description="Timestamp of processing")

    @model_validator(mode="after")
    def validate_prices(self) -> "KlineData":
        """Custom validator for price relationship"""
        if self.high < self.low:
            raise ValueError(
                f"High price {self.high} is less than low price {self.low}"
            )
        if self.close > self.high:
            raise ValueError(
                f"Close price {self.close} is greater than high price {self.high}"
            )
        if self.close < self.low:
            raise ValueError(
                f"Close price {self.close} is less than low price {self.low}"
            )
        return self


class HistoricalData(BaseModel):
    """Model for a batch of historical data"""

    symbol: str
    data: List[KlineData]

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "data": [{"symbol": "BTCUSDT", "close": 50000.0, "open": 49000.0}],
            }
        }


class StreamingData(BaseModel):
    """
    Model for single streaming data point,
    inheriting most fields from KlineData
    """

    symbol: str
    open_time: int
    close: float
    ts: datetime
    is_closed: bool = Field(
        ..., description="WebSocket flag indicating if the kline is closed"
    )
