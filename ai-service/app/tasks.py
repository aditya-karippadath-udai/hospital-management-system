from .celery_app import celery_app
from .ingestion.parser import DocumentParser
from .ingestion.processor import DocumentProcessor
from .ingestion.embeddings import EmbeddingEngine
from .ingestion.vector_store import VectorStore
import logging
import os

logger = logging.getLogger(__name__)

# Initialize components (lazily or as singletons)
processor = DocumentProcessor()
embedding_engine = EmbeddingEngine()
vector_store = VectorStore()

@celery_app.task(bind=True, max_retries=3)
def ingest_document_task(self, file_path: str, metadata: dict, remove_phi: bool = False):
    """
    Orchestrates the full ingestion pipeline for a single document.
    """
    logger.info(f"Starting ingestion for: {file_path}")
    
    try:
        # 1. Parse
        raw_text = DocumentParser.parse(file_path)
        
        # 2. Clean & Anonymize
        clean_text = processor.clean_text(raw_text)
        if remove_phi:
            clean_text = processor.remove_phi(clean_text)
            
        # 3. Chunk
        chunks = processor.chunk_text(clean_text)
        logger.info(f"Document split into {len(chunks)} chunks.")
        
        # 4. Generate Embeddings (Batched)
        embeddings = embedding_engine.generate(chunks)
        
        # 5. Store in Qdrant
        vector_store.upsert_chunks(chunks, embeddings, metadata)
        
        logger.info(f"Successfully ingested and indexed: {file_path}")
        return {"status": "success", "chunks": len(chunks), "file": file_path}

    except Exception as exc:
        logger.error(f"Ingestion failed for {file_path}: {exc}")
        # Retry logic for transient failures (e.g., DB connection)
        raise self.retry(exc=exc, countdown=60)
