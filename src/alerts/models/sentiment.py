"""
Data models for sentiment analysis and storage.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SentimentResult(BaseModel):
    """Result from sentiment analysis provider."""
    labels: List[str] = Field(..., description = "Sentiment labels (e.g., ['bullish', 'bearish', 'neutral'])")
    scores: List[float] = Field(..., description = "Confidence scores for each label (0-1)")
    text: str = Field(..., description = "Original text that was analyzed")
    provider: str = Field(..., description = "Provider name (mistral/huggingface)")


    @property
    def top_label(self) -> Optional[str]:
        """Get label with highest confidence."""
        if not self.labels or not self.scores:
            return None
        max_idx = self.scores.index(max(self.scores))
        return self.labels[max_idx]


    @property
    def top_confidence(self) -> Optional[float]:
        """Get confidence score for top label."""
        if not self.scores:
            return None
        return max(self.scores)


class SentimentRecord(BaseModel):
    """Record stored in MongoDB time series collection."""
    timestamp: datetime = Field(..., description = "When sentiment was generated (UTC)")
    symbol: str = Field(..., description = "Trading pair (e.g., BTC/USDT)")
    sentiment_label: str = Field(..., description = "Top sentiment label")
    confidence: float = Field(..., ge = 0, le = 1, description = "Confidence score (0-1)")
    text: str = Field(..., description = "Original message/text")
    provider: str = Field(..., description = "Sentiment provider")
    price: float = Field(..., gt = 0, description = "Price at time of sentiment")
    exchange: str = Field(..., description = "Exchange where price was from")
    metadata: Dict[str, Any] = Field(default_factory = dict, description = "Additional metadata")

    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SentimentTrend(BaseModel):
    """Aggregated sentiment trend data."""
    timestamp: datetime
    symbol: str
    sentiment_label: str
    confidence: float
    price: float
    exchange: str
