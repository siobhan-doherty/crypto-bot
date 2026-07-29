import numpy as np
import pickle
import logging
from sklearn.cluster import HDBSCAN, KMeans
from pathlib import Path

logger = logging.getLogger(__name__)


class PatternClusterer:
    """
    clusters pattern embeddings into regimes.
    uses HDBSCAN by default for auto discovery of cluster count.
    """
    def __init__(
        self,
        min_cluster_size: int = 5,
        metric: str = "euclidean",
        model_path: str = "src/pattern_analytics/models/",
    ):
        self.min_cluster_size = min_cluster_size
        self.metric = metric
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents = True, exist_ok = True)
        self.clusterer = None
        self.cluster_labels = None
        self.cluster_centroids = None  # for K‑means
        self.is_fitted = False
        self.n_clusters = 0


    def fit(self, embeddings: np.ndarray) -> np.ndarray:
        """cluster embeddings and return labels."""
        if len(embeddings) < self.min_cluster_size:
            logger.warning(f"Only {len(embeddings)} samples, need at least {self.min_cluster_size}")
            self.cluster_labels = np.array([-1] * len(embeddings))
            self.is_fitted = True
            return self.cluster_labels

        self.clusterer = HDBSCAN(min_cluster_size = self.min_cluster_size, metric = self.metric)
        self.cluster_labels = self.clusterer.fit_predict(embeddings)
        self.is_fitted = True
        self.n_clusters = len(set(self.cluster_labels) - {-1})
        logger.info(f"Found {self.n_clusters} clusters (outliers: {sum(self.cluster_labels == -1)})")
        self._save()
        return self.cluster_labels


    def predict(self, embedding: np.ndarray) -> int:
        """predict cluster for single embedding."""
        if not self.is_fitted:
            raise RuntimeError("Clusterer not fitted, call fit() first")
        if self.clusterer is None:
            return -1

        # approximate nearest neighbour, for production store centroids and use K‑means or KNN classifier.
        return self._predict_approximate(embedding)


    def _predict_approximate(self, embedding: np.ndarray) -> int:
        """approximate prediction using nearest centroid, if available."""
        if self.cluster_centroids is not None:
            from scipy.spatial.distance import cdist

            distances = cdist(embedding.reshape(1, -1), self.cluster_centroids)
            return np.argmin(distances)

        return -1


    def fit_kmeans_from_hdbscan(self, embeddings: np.ndarray) -> None:
        """train K‑means classifier on HDBSCAN labels for fast prediction."""
        if not self.is_fitted or self.cluster_labels is None:
            raise RuntimeError("Must fit HDBSCAN first")

        valid = self.cluster_labels != -1
        n_valid = sum(valid)
        if n_valid < 10:  # need enough samples
            logger.warning(f"Only {n_valid} non‑outlier samples, skipping K‑means training")
            return

        # reduce cluster count if too many for data
        n_clusters = min(self.n_clusters, n_valid // 5)
        if n_clusters < 2:
            logger.warning("Too few clusters, skipping K‑means training")
            return

        try:
            from sklearn.cluster import KMeans

            kmeans = KMeans(n_clusters=n_clusters, random_state = 42, n_init = 10)
            kmeans.fit(embeddings[valid])
            self.cluster_centroids = kmeans.cluster_centers_
            self.n_clusters = n_clusters
            self._save()
            logger.info(f"K‑means trained with {n_clusters} centroids")
        except Exception as e:
            logger.warning(f"K‑means training failed – using HDBSCAN only: {e}")
            self.cluster_centroids = None


    def _save(self) -> None:
        """save clusterer to disk."""
        with open(self.model_path / "clusterer.pkl", "wb") as f:
            pickle.dump({
                "cluster_labels": self.cluster_labels,
                "cluster_centroids": self.cluster_centroids,
                "n_clusters": self.n_clusters,
            }, f)
        logger.info(f"Clusterer saved to {self.model_path / 'clusterer.pkl'}")


    def load(self) -> None:
        """load fitted clusterer from disk."""
        path = self.model_path / "clusterer.pkl"
        if not path.exists():
            logger.warning(f"No clusterer found at {path}")
            return

        with open(path, "rb") as f:
            data = pickle.load(f)
        self.cluster_labels = data["cluster_labels"]
        self.cluster_centroids = data.get("cluster_centroids")
        self.n_clusters = data.get("n_clusters", 0)
        self.is_fitted = True
        logger.info(f"Clusterer loaded from {path} (n_clusters={self.n_clusters})")
