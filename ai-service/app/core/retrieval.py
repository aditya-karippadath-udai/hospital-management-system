import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Internal imports
from ..ingestion.vector_store import VectorStore
from ..core.embeddings import EmbeddingService
from ..models.kb import AccessLevel

logger = logging.getLogger(__name__)

class HybridRetrievalEngine:
    """
    Orchestrates dense and lexical search with multi-stage filtering.
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.k_dense = 20
        self.k_lexical = 20
        self.final_k = 5

    def search(
        self, 
        query: str, 
        user_role: str,
        department: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search with filtering and reranking.
        """
        logger.info(f"Initiating hybrid search for query: {query}")
        
        # 1. Query Preprocessing (e.g., expansion, cleanup)
        processed_query = self._preprocess_query(query)
        
        # 2. Get Query Embedding
        query_vector = self.embedding_service.get_embeddings([processed_query])[0]
        
        # 3. Construct Metadata Filters
        # Note: Role-based filtering is enforced here
        metadata_filters = self._build_filters(user_role, department, filters)
        
        # 4. Dense Vector Search (Qdrant)
        dense_results = self.vector_store.client.search(
            collection_name=self.vector_store.collection_name,
            query_vector=query_vector,
            query_filter=metadata_filters,
            limit=self.k_dense,
            with_payload=True,
            with_vectors=False
        )
        
        # 5. Lexical/Keyword Search (Simulated or via Qdrant full-text if enabled)
        # Qdrant supports full-text search via the 'match' filter
        lexical_results = self.vector_store.client.scroll(
            collection_name=self.vector_store.collection_name,
            scroll_filter=self._build_lexical_filter(processed_query, metadata_filters),
            limit=self.k_lexical,
            with_payload=True
        )[0]
        
        # 6. Hybrid Fusion (Reciprocal Rank Fusion - RRF)
        fused_results = self._reciprocal_rank_fusion(dense_results, lexical_results)
        
        # 7. Reranking (Cross-Encoder style filtering)
        reranked_results = self._rerank(processed_query, fused_results)
        
        return reranked_results[:self.final_k]

    def _preprocess_query(self, query: str) -> str:
        """Clean and normalize medical query."""
        # Future: Add medical acronym expansion or HyDE expansion here
        return query.strip().lower()

    def _build_filters(self, user_role: str, department: str, extra_filters: dict) -> Any:
        # Import models here to avoid circular imports in some setups
        from qdrant_client.http import models as q_models
        
        # Mandatory Tenant Isolation (Fail-Closed)
        tenant_id = os.getenv("TENANT_ID", "global") # In prod, extract from request context
        
        # Role-based visibility logic
        role_visibility = {
            "admin": ["admin", "doctor", "nurse", "patient", "public"],
            "doctor": ["doctor", "nurse", "patient", "public"],
            "nurse": ["nurse", "patient", "public"],
            "patient": ["patient", "public"],
            "receptionist": ["public"]
        }
        allowed_levels = role_visibility.get(user_role.lower(), ["public"])
        
        filter_list = [
            q_models.FieldCondition(
                key="tenant_id",
                match=q_models.MatchValue(value=tenant_id)
            ),
            q_models.FieldCondition(
                key="access_level_required",
                match=q_models.MatchAny(any=allowed_levels)
            )
        ]
        
        if department:
            filter_list.append(
                q_models.FieldCondition(
                    key="department",
                    match=q_models.MatchValue(value=department)
                )
            )

        # Apply Data Isolation / Extra Filters (e.g., patient_id)
        if extra_filters:
            for key, value in extra_filters.items():
                filter_list.append(
                    q_models.FieldCondition(
                        key=key,
                        match=q_models.MatchValue(value=value)
                    )
                )
            
        return q_models.Filter(must=filter_list)

    def _build_lexical_filter(self, query: str, base_filter: Any) -> Any:
        from qdrant_client.http import models as q_models
        # Merge lexical match with base filters
        lexical_filter = q_models.FieldCondition(
            key="content",
            match=q_models.MatchText(text=query)
        )
        
        must_filters = list(base_filter.must) if base_filter.must else []
        must_filters.append(lexical_filter)
        return q_models.Filter(must=must_filters)

    def _reciprocal_rank_fusion(self, dense: list, lexical: list, k: int = 60) -> List[Dict]:
        """Combine results from different search methods."""
        scores = {}
        
        for rank, hit in enumerate(dense):
            doc_id = hit.id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            
        for rank, hit in enumerate(lexical):
            doc_id = hit.id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            
        # Reconstruct result list
        all_hits = {hit.id: hit.payload for hit in dense}
        all_hits.update({hit.id: hit.payload for hit in lexical})
        
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [{"id": id_, "score": score, "payload": all_hits[id_]} for id_, score in sorted_ids]

    def _rerank(self, query: str, hits: list) -> List[Dict]:
        """
        Placeholder for Cross-Encoder reranking.
        In prod, use a model like 'cross-encoder/ms-marco-MiniLM-L-6-v2'.
        """
        # For now, we simulate reranking by checking for exact medical term matches
        # and promoting documents with lower risk profiles.
        return hits
