import numpy as np
import pandas as pd
from typing import List, Dict
from scipy.stats import skew, kurtosis


class FeatureExtractor:
    """
    Extracts statistical and technical features from price window.
    feature engineering layer, quality of features determines quality of clustering.
    """
    @staticmethod
    def extract_features(df: pd.DataFrame) -> Dict[str, float]:
        """extract features from DataFrame with 'open', 'high', 'low', 'close', 'volume'."""
        if df.empty or len(df) < 10:
            return {}

        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        volume = df["volume"].values
        returns = np.diff(np.log(close))
        features = {
            # price statistics
            "mean_close": np.mean(close),
            "std_close": np.std(close),
            "skew_close": skew(close),
            "kurtosis_close": kurtosis(close),
            # returns statistics
            "mean_return": np.mean(returns),
            "std_return": np.std(returns),
            "skew_return": skew(returns),
            "kurtosis_return": kurtosis(returns),
            # price range
            "high_low_ratio": np.max(high) / np.min(low) if np.min(low) > 0 else 1.0,
            "close_open_ratio": close[-1] / close[0] if close[0] > 0 else 1.0,
            # volatility
            "volatility": np.std(returns) * np.sqrt(252),
            # volume
            "mean_volume": np.mean(volume),
            "volume_volatility": np.std(volume),
            # trend indicators
            "momentum": close[-1] / close[0] - 1 if close[0] > 0 else 0,
            "max_drawdown": (np.max(close) - np.min(close)) / np.max(close) if np.max(close) > 0 else 0,
            # shape indicators
            "linear_trend": np.polyfit(range(len(close)), close, 1)[0],  # slope of linear fit
            # RSI approxmation, 14-period equivalent using average gain/loss
            "rsi": FeatureExtractor._calculate_rsi(close),
            # MACD approximation, 12-period EMA 26-period EMA
            "macd": FeatureExtractor._calculate_macd(close),
        }

        return features


    @staticmethod
    def window_to_feature_vector(df: pd.DataFrame) -> np.ndarray:
        """convert price window to flat feature vector."""
        features = FeatureExtractor.extract_features(df)
        if not features:
            return np.array([])

        return np.array(list(features.values()))


    @staticmethod
    def _calculate_rsi(close: np.ndarray, period: int = 14) -> float:
        """calculate approximate RSI for close prices."""
        if len(close) < period + 1:
            return 50.0  # neutral fallback
        
        delta = np.diff(close)
        gains = delta[delta > 0]
        losses = -delta[delta < 0]
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 1  # avoid division by zero
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))


    @staticmethod
    def _calculate_macd(close: np.ndarray, fast: int = 12, slow: int = 26) -> float:
        """calculate approximate MACD, fast EMA - slow EMA for close prices."""
        if len(close) < slow:
            return 0.0

        # using pandas for EMA calculation for simplicity
        series = pd.Series(close)
        ema_fast = series.ewm(span = fast, adjust = False).mean().iloc[-1]
        ema_slow = series.ewm(span = slow, adjust = False).mean().iloc[-1]
        return ema_fast - ema_slow
