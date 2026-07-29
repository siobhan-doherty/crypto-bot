import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from src.pattern_analytics.feature_extractor import FeatureExtractor
from src.pattern_analytics.embedder import PatternEmbedder
from src.pattern_analytics.clusterer import PatternClusterer
import logging

logger = logging.getLogger(__name__)


class PatternDetector:
    """real time pattern detection: takes price window, returns cluster label and metadata."""
    def __init__(self):
        self.embedder = PatternEmbedder()
        self.clusterer = PatternClusterer()
        self.embedder.load()
        self.clusterer.load()


    def detect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect pattern in price window.
        Returns:
            {
                "cluster_id": int,           # -1 if outlier
                "embedding": list[float],
                "feature_vector": list[float],
                "confidence": float,         # distance to cluster centroid (if available)
            }
        """
        if df.empty or len(df) < 10:
            return {"cluster_id": -1, "embedding": None, "feature_vector": None}

        features = FeatureExtractor.extract_features(df)
        feature_vector = np.array(list(features.values()))
        if not self.embedder.is_fitted:
            # fallback if not trained, just return features
            return {
                "cluster_id": -1,
                "embedding": None,
                "feature_vector": feature_vector.tolist(),
            }
        try:
            embedding = self.embedder.embed(feature_vector)
            cluster_id = self.clusterer.predict(embedding)
        except Exception as e:
            logger.warning(f"Pattern detection failed: {e}")
            cluster_id = -1
            embedding = None

        return {
            "cluster_id": cluster_id,
            "embedding": embedding.tolist(),
            "feature_vector": feature_vector.tolist(),
            "confidence": 1.0,  # placeholder, can compute distance to centroid
        }


    def add_pattern_context_to_alert(self, alert_message: str, pattern_info: Dict[str, Any]) -> str:
        """enrich alert message with pattern context."""
        cluster_id = pattern_info.get("cluster_id")
        if cluster_id is None or cluster_id == -1:
            return alert_message

        # could map cluster IDs to human readable labels
        cluster_labels = {
            0: "Breakout (bullish)",
            1: "Breakdown (bearish)",
            2: "Range consolidation",
            3: "Volatile spike",
        }
        label = cluster_labels.get(cluster_id, f"Pattern {cluster_id}")
        return alert_message + f"\n\n *Pattern:* {label} (cluster {cluster_id})"
