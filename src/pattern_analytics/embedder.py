import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PatternEmbedder:
    """
    embeds high dimensional feature vectors into low dimensional space.
    uses PCA by default, then swap in PyTorch autoencoder easily.
    """
    def __init__(self, embedding_dim: int = 16, model_path: str = "src/pattern_analytics/models/"):
        self.embedding_dim = embedding_dim
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents = True, exist_ok = True)
        self.scaler = None
        self.pca = None
        self.is_fitted = False


    def fit(self, feature_vectors: np.ndarray) -> None:
        """fit PCA on historical feature vectors."""
        if len(feature_vectors) < 2:
            raise ValueError("Need at least 2 samples to fit PCA")
        self.scaler = StandardScaler()
        scaled = self.scaler.fit_transform(feature_vectors)
        self.pca = PCA(n_components = self.embedding_dim)
        self.pca.fit(scaled)
        self.is_fitted = True
        logger.info(f"Fitted PCA with {self.embedding_dim} components")
        self._save()


    def embed(self, feature_vector: np.ndarray) -> np.ndarray:
        """embed a single feature vector."""
        if not self.is_fitted or self.scaler is None or self.pca is None:
            raise RuntimeError("Embedder not fitted, call fit() first")
        scaled = self.scaler.transform(feature_vector.reshape(1, -1))
        return self.pca.transform(scaled)[0]


    def embed_batch(self, feature_vectors: np.ndarray) -> np.ndarray:
        """embed multiple feature vectors."""
        if not self.is_fitted or self.scaler is None or self.pca is None:
            raise RuntimeError("Embedder not fitted, call fit() first")
        scaled = self.scaler.transform(feature_vectors)
        return self.pca.transform(scaled)


    def _save(self) -> None:
        """save fitted embedder to disk."""
        with open(self.model_path / "embedder.pkl", "wb") as f:
            pickle.dump({
                "scaler": self.scaler,
                "pca": self.pca,
                "embedding_dim": self.embedding_dim,
            }, f)
        logger.info(f"Embedder saved to {self.model_path / 'embedder.pkl'}")


    def load(self) -> None:
        """load fitted embedder from disk."""
        path = self.model_path / "embedder.pkl"
        if not path.exists():
            logger.warning(f"No embedder found at {path}")
            return

        with open(path, "rb") as f:
            data = pickle.load(f)
        self.scaler = data["scaler"]
        self.pca = data["pca"]
        self.embedding_dim = data["embedding_dim"]
        self.is_fitted = True
        logger.info(f"Embedder loaded from {path}")
