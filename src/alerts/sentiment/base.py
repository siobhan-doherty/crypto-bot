from abc import ABC, abstractmethod
from typing import Optional


class SentimentProvider(ABC):
    @abstractmethod
    def classify(self, text: str) -> Optional[dict]:
        """Return sentiment labels with scores."""
        pass
