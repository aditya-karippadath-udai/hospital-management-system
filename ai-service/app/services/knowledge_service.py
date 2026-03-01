import logging
import re
from datetime import datetime, timezone

from ..services.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Chunking config
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # overlap between chunks


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks on sentence boundaries when possible.
    Falls back to character-level splitting for very long sentences.
    """
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks: list[str] = []
    current_chunk = ""

    for sentence in sentences:
        # If a single sentence exceeds chunk_size, hard-split it
        if len(sentence) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            for i in range(0, len(sentence), chunk_size - overlap):
                chunks.append(sentence[i : i + chunk_size].strip())
            continue

        if len(current_chunk) + len(sentence) + 1 > chunk_size:
            chunks.append(current_chunk.strip())
            # Keep overlap from the tail of the previous chunk
            current_chunk = current_chunk[-overlap:] + " " + sentence if overlap else sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if len(c) >= 10]  # discard tiny fragments


def ingest_knowledge(
    title: str,
    category: str,
    description: str,
    created_by: str,
) -> dict:
    """
    Chunk, embed, and store a knowledge document in FAISS.
    Returns summary stats.
    """
    chunks = _chunk_text(description)

    stored = 0
    skipped = 0

    for i, chunk in enumerate(chunks):
        meta = {
            "type": category,
            "source": title,
            "created_by": created_by,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        added = VectorStore.add_document(text=chunk, metadata=meta)
        if added:
            stored += 1
        else:
            skipped += 1

    # Persist immediately so data survives a crash
    if stored > 0:
        VectorStore.save_index()

    logger.info(
        "KNOWLEDGE_ADDED  title=%s  category=%s  chunks=%d  stored=%d  skipped=%d  by=%s",
        title, category, len(chunks), stored, skipped, created_by,
    )

    return {
        "chunks_stored": stored,
        "duplicates_skipped": skipped,
        "total_vectors": VectorStore.count(),
    }
