from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """Interface for Qdrant vector database."""
    
    def __init__(self):
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
        self.collection_name = "medical_knowledge"
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            # Using 1024 for BGE-M3 (matches dimensionality)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            )

    def upsert_chunks(self, chunks: list[str], embeddings: list[list[float]], metadata: dict):
        """Batch upsert points into Qdrant."""
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={**metadata, "content": chunk}
            )
            for chunk, emb in zip(chunks, embeddings)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
