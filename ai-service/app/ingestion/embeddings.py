from ..core.embeddings import EmbeddingService
import logging

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    """Generates embeddings for medical text chunks using the modular service."""
    
    def __init__(self):
        self.service = EmbeddingService()

    def generate(self, texts: list[str]) -> list[list[float]]:
        """Batch generate embeddings with caching and fallback."""
        try:
            return self.service.get_embeddings(texts)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
