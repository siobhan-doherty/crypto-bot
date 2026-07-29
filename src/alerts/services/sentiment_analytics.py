"""
Analytics service for sentiment data.
Provides correlation analysis, trend detection and model training data.
"""
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler
from src.alerts.repositories.sentiment_repository import SentimentRepository

logger = logging.getLogger(__name__)


class SentimentAnalyticsService:
    """
    Analytics service for sentiment data analysis.
    Capabilities:
    - Correlation analysis between sentiment and price
    - Trend detection
    - Data preparation for ML model training
    - Anomaly detection
    """
    def __init__(self, mongo_uri: str):
        self.repo = SentimentRepository(mongo_uri)


    def calculate_correlation(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        time_window: str = "1h",
    ) -> Dict[str, Any]:
        """
        Calculate correlation between sentiment and price.
        Args:
            symbol: Trading pair
            start_time: Start of analysis period
            end_time: End of analysis period
            time_window: Aggregation window
        Returns:
            Dictionary with correlation metrics
        """
        # Get aggregated data
        correlated_data = self.repo.get_sentiment_price_correlation(
            symbol = symbol,
            start_time = start_time,
            end_time = end_time,
            time_window = time_window,
        )
        if len(correlated_data) < 2:
            return {
                "symbol": symbol,
                "period": f"{start_time} to {end_time}",
                "pearson": None,
                "spearman": None,
                "sample_size": len(correlated_data),
                "message": "Insufficient data for correlation",
            }
        # extract price and sentiment arrays
        prices = []
        sentiment_scores = []

        for record in correlated_data:
            # Map sentiment to numerical score
            sentiment_map = {
                "bullish": 1.0,
                "neutral": 0.0,
                "bearish": -1.0,
            }
            sentiment_score = sentiment_map.get(record.get("sentiment_label", "neutral"), 0.0)
            sentiment_scores.append(sentiment_score)
            prices.append(record.get("price", 0.0))

        # calculate correlations
        pearson = pearsonr(prices, sentiment_scores)
        spearman = spearmanr(prices, sentiment_scores)

        return {
            "symbol": symbol,
            "period": f"{start_time} to {end_time}",
            "pearson_correlation": pearson[0],
            "pearson_p_value": pearson[1],
            "spearman_correlation": spearman[0],
            "spearman_p_value": spearman[1],
            "sample_size": len(correlated_data),
            "data_points": correlated_data,
        }


    def detect_sentiment_trend(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        window_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Detect sentiment trends using moving averages.
        Args:
            symbol: Trading pair
            start_time: Start of analysis period
            end_time: End of analysis period
            window_size: Size of moving average window
        Returns:
            Trend analysis results
        """
        sentiment_data = self.repo.get_sentiment_trend(
            symbol = symbol,
            start_time = start_time,
            end_time = end_time,
        )
        if not sentiment_data:
            return {"symbol": symbol, "trend": None, "message": "No data"}

        # convert to DataFrame
        df = pd.DataFrame(sentiment_data)
        # map sentiment to numerical
        sentiment_map = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
        df["sentiment_score"] = df["sentiment_label"].map(sentiment_map)
        # calculate moving average
        df["sentiment_ma"] = df["sentiment_score"].rolling(window = window_size).mean()
        df["price_ma"] = df["price"].rolling(window = window_size).mean()
        # calculate trend direction
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        sentiment_trend = "neutral"
        if latest["sentiment_ma"] > prev["sentiment_ma"]:
            sentiment_trend = "improving"
        elif latest["sentiment_ma"] < prev["sentiment_ma"]:
            sentiment_trend = "deteriorating"

        price_trend = "neutral"
        if latest["price_ma"] > prev["price_ma"]:
            price_trend = "rising"
        elif latest["price_ma"] < prev["price_ma"]:
            price_trend = "falling"

        return {
            "symbol": symbol,
            "period": f"{start_time} to {end_time}",
            "current_sentiment": latest["sentiment_label"],
            "current_sentiment_score": latest["sentiment_score"],
            "current_price": latest["price"],
            "sentiment_trend": sentiment_trend,
            "price_trend": price_trend,
            "data_points": len(df),
            "chart_data": df[["timestamp", "sentiment_ma", "price_ma"]].to_dict("records"),
        }


    def prepare_training_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        lookback_window: int = 10,
        forecast_horizon: int = 1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare feature matrix (X) and target vector (y) for ML model training.
        Uses sentiment as features to predict future price movements.
        Args:
            symbol: Trading pair
            start_time: Start of training period
            end_time: End of training period
            lookback_window: Number of past sentiment readings to use as features
            forecast_horizon: How many periods ahead to predict
        Returns:
            Tuple of (X_features, y_targets)
        """
        correlated_data = self.repo.get_sentiment_price_correlation(
            symbol = symbol,
            start_time = start_time,
            end_time = end_time,
            time_window = "1h",
        )        
        if len(correlated_data) < lookback_window + forecast_horizon:
            return np.array([]), np.array([])

        # convert to DataFrame
        df = pd.DataFrame(correlated_data)
        # map sentiment to numerical
        sentiment_map = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
        df["sentiment_score"] = df["sentiment_label"].map(sentiment_map).fillna(0.0)
        # calculate price returns
        df["price_return"] = df["price"].pct_change().fillna(0.0)
        # create feature matrix
        X = []
        y = []

        for i in range(lookback_window, len(df) - forecast_horizon):
            # features past sentiment scores
            features = df["sentiment_score"].iloc[i - lookback_window : i].values
            X.append(features)
            # target future price return
            future_return = df["price_return"].iloc[i + forecast_horizon]
            y.append(future_return)

        return np.array(X), np.array(y)


    def get_sentiment_anomalies(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        z_threshold: float = 3.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect sentiment anomalies using z-score method.
        Args:
            symbol: Trading pair
            start_time: Start of analysis period
            end_time: End of analysis period
            z_threshold: Z-score threshold for anomaly detection
        Returns:
            List of anomalous sentiment records
        """
        sentiment_data = self.repo.get_sentiment_trend(
            symbol = symbol,
            start_time = start_time,
            end_time = end_time,
        )
        if not sentiment_data:
            return []

        df = pd.DataFrame(sentiment_data)
        sentiment_map = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
        df["sentiment_score"] = df["sentiment_label"].map(sentiment_map).fillna(0.0)
        # calculate z-scores
        mean = df["sentiment_score"].mean()
        std = df["sentiment_score"].std()
        if std == 0:
            return []

        df["z_score"] = (df["sentiment_score"] - mean) / std
        anomalies = df[abs(df["z_score"]) > z_threshold]
        return anomalies.to_dict("records")
