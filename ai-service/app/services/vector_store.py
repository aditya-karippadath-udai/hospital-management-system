import os
import json
import hashlib
import threading
import logging
import time
from datetime import datetime, timezone
from typing import Any

import faiss
import numpy as np

from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Default persistence paths
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "vector_store")
INDEX_PATH = os.path.join(BASE_DIR, "index.faiss")
META_PATH = os.path.join(BASE_DIR, "metadata.json")


class VectorStore:
    """
    Thread-safe FAISS vector store with JSON metadata persistence.
    Uses Inner Product (IP) on L2-normalised vectors ≡ cosine similarity.
    """

    _lock = threading.Lock()
    _index: faiss.IndexFlatIP | None = None
    _metadata: list[dict] = []          # parallel list — position maps to FAISS row
    _doc_hashes: set[str] = set()       # fast duplicate check

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @classmethod
    def initialize(cls) -> None:
        """Load existing index from disk or create a fresh one."""
        os.makedirs(BASE_DIR, exist_ok=True)
        EmbeddingService.initialize()
        dim = EmbeddingService.dimension()

        if os.path.isfile(INDEX_PATH) and os.path.isfile(META_PATH):
            cls.load_index()
            logger.info(
                "VectorStore: loaded %d vectors from disk.", cls._index.ntotal
            )
        else:
            cls._index = faiss.IndexFlatIP(dim)
            cls._metadata = []
            cls._doc_hashes = set()
            logger.info("VectorStore: created new index (dim=%d).", dim)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @classmethod
    def add_document(
        cls,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Embed *text*, store vector + metadata.

        Required metadata keys:  type, source, created_by
        Returns False if duplicate or empty.
        """
        if not text or not text.strip():
            logger.warning("VectorStore: rejected empty text.")
            return False

        # Duplicate guard (content hash)
        doc_hash = hashlib.sha256(text.encode()).hexdigest()
        with cls._lock:
            if doc_hash in cls._doc_hashes:
                logger.info("VectorStore: duplicate skipped (%s…)", doc_hash[:12])
                return False

        # Embed
        vector = EmbeddingService.encode(text)          # shape (1, dim)
        if vector is None or vector.size == 0:
            logger.warning("VectorStore: empty embedding — skipping.")
            return False

        # Build metadata record
        meta = metadata.copy() if metadata else {}
        meta.setdefault("type", "hospital_info")
        meta.setdefault("source", "unknown")
        meta.setdefault("created_by", "system")
        meta["timestamp"] = datetime.now(timezone.utc).isoformat()
        meta["text"] = text
        meta["hash"] = doc_hash

        with cls._lock:
            cls._index.add(vector)
            cls._metadata.append(meta)
            cls._doc_hashes.add(doc_hash)

        return True

    @classmethod
    def search(
        cls,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Return top-k results as list of {score, text, metadata}.
        """
        if cls._index is None or cls._index.ntotal == 0:
            return []

        vector = EmbeddingService.encode(query)

        with cls._lock:
            scores, indices = cls._index.search(vector, min(top_k, cls._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = cls._metadata[idx].copy()
            text = meta.pop("text", "")
            results.append({"score": float(score), "text": text, "metadata": meta})

        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @classmethod
    def save_index(cls) -> None:
        os.makedirs(BASE_DIR, exist_ok=True)
        with cls._lock:
            faiss.write_index(cls._index, INDEX_PATH)
            with open(META_PATH, "w", encoding="utf-8") as f:
                json.dump(cls._metadata, f, ensure_ascii=False, indent=2)
        logger.info("VectorStore: saved %d vectors to disk.", cls._index.ntotal)

    @classmethod
    def load_index(cls) -> None:
        cls._index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "r", encoding="utf-8") as f:
            cls._metadata = json.load(f)
        cls._doc_hashes = {m.get("hash", "") for m in cls._metadata}
        logger.info("VectorStore: loaded %d vectors.", cls._index.ntotal)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def count(cls) -> int:
        return cls._index.ntotal if cls._index else 0

    @classmethod
    def is_ready(cls) -> bool:
        return cls._index is not None

    # ------------------------------------------------------------------
    # Integrity & Rebuild
    # ------------------------------------------------------------------
    @classmethod
    def verify_integrity(cls) -> tuple[bool, str]:
        """
        Run integrity checks on the loaded index.

        Returns (ok, reason).
        """
        if cls._index is None:
            return False, "index_not_loaded"

        # Check 1: metadata count must match index row count
        if cls._index.ntotal != len(cls._metadata):
            return False, (
                f"row_mismatch: index={cls._index.ntotal} meta={len(cls._metadata)}"
            )

        # Check 2: dimension sanity
        try:
            expected_dim = EmbeddingService.dimension()
            if cls._index.d != expected_dim:
                return False, (
                    f"dim_mismatch: index={cls._index.d} expected={expected_dim}"
                )
        except Exception:
            pass  # embedding model not loaded yet — skip dim check

        # Check 3: probe search should not crash
        try:
            if cls._index.ntotal > 0:
                dummy = np.zeros((1, cls._index.d), dtype=np.float32)
                cls._index.search(dummy, 1)
        except Exception as e:
            return False, f"probe_failed: {e}"

        return True, "ok"

    @classmethod
    def rebuild_index(cls) -> None:
        """
        Re-create the FAISS index from stored metadata texts.
        Used when corruption is detected.
        """
        logger.warning("VectorStore: rebuilding index from metadata …")
        dim = EmbeddingService.dimension()
        new_index = faiss.IndexFlatIP(dim)
        valid_meta: list[dict] = []
        valid_hashes: set[str] = set()

        for meta in cls._metadata:
            text = meta.get("text", "")
            if not text:
                continue
            try:
                vec = EmbeddingService.encode(text)
                new_index.add(vec)
                valid_meta.append(meta)
                valid_hashes.add(meta.get("hash", ""))
            except Exception as e:
                logger.warning("VectorStore: skip doc during rebuild: %s", e)

        with cls._lock:
            cls._index = new_index
            cls._metadata = valid_meta
            cls._doc_hashes = valid_hashes

        cls.save_index()
        logger.info(
            "VectorStore: rebuilt index with %d vectors.", new_index.ntotal
        )

    @classmethod
    def get_health_info(cls) -> dict:
        """Structured health snapshot for /health/ai."""
        ok, reason = cls.verify_integrity() if cls._index else (False, "not_loaded")
        return {
            "vector_store_ready": cls.is_ready(),
            "vector_index_size": cls.count(),
            "metadata_count": len(cls._metadata),
            "integrity_ok": ok,
            "integrity_detail": reason,
        }
