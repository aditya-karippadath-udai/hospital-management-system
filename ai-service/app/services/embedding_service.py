import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model ID — runs fully offline after first download
MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Thin wrapper around sentence-transformers.
    Loads the model once and exposes encode().
    """

    _model: SentenceTransformer | None = None

    @classmethod
    def initialize(cls, model_name: str = MODEL_NAME) -> None:
        if cls._model is not None:
            return
        logger.info("EmbeddingService: loading %s …", model_name)
        cls._model = SentenceTransformer(model_name)
        logger.info("EmbeddingService: ready  (dim=%d)", cls._model.get_sentence_embedding_dimension())

    @classmethod
    def encode(cls, texts: str | list[str]) -> np.ndarray:
        """Return L2-normalised float32 embeddings."""
        if cls._model is None:
            raise RuntimeError("EmbeddingService not initialized.")
        if isinstance(texts, str):
            texts = [texts]
        vectors = cls._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.astype(np.float32)

    @classmethod
    def dimension(cls) -> int:
        if cls._model is None:
            raise RuntimeError("EmbeddingService not initialized.")
        return cls._model.get_sentence_embedding_dimension()
