"""
Unified AI Pipeline
===================
Single entry-point that orchestrates every stage of query processing:

    Guardrails → Triage → Intent (ERP / RAG / General)
        → Context Assembly (token-limited)
            → LLaMA Inference (timeout-protected)
                → PHI Scrub → Audit Log → Response
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.emergency import EmergencyDetector, Severity
from ..core.guardrails import GuardrailService
from ..core.phi import PHIScrubber
from ..core.structured_query import try_structured_query
from ..services.llama_service import LlamaService
from ..services.vector_store import VectorStore
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────

MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "3000"))   # ~750 tokens
MAX_TOKENS        = int(os.getenv("LLM_MAX_TOKENS", "1024"))
TEMPERATURE       = float(os.getenv("LLM_TEMPERATURE", "0.3"))
FAISS_TOP_K       = int(os.getenv("FAISS_TOP_K", "5"))
LLM_TIMEOUT       = float(os.getenv("LLM_TIMEOUT", "30.0"))
RETRIEVAL_TIMEOUT  = float(os.getenv("RETRIEVAL_TIMEOUT", "5.0"))


# ─── Data Structures ─────────────────────────────────────────────────────────

class QueryType(str, Enum):
    EMERGENCY   = "emergency"
    ERP         = "structured_erp"
    KNOWLEDGE   = "knowledge_rag"
    GENERAL     = "general_llm"
    FALLBACK    = "fallback"


@dataclass
class PipelineResult:
    query: str                  = ""
    response: str               = ""
    query_type: QueryType       = QueryType.GENERAL
    status: str                 = "completed"
    citations: list[str]        = field(default_factory=list)
    vector_hits: int            = 0
    erp_used: bool              = False
    response_time_ms: float     = 0.0
    error: str | None           = None


# ─── Context Helpers ──────────────────────────────────────────────────────────

def _truncate_context(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Hard-truncate context to stay inside the model's token budget."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]        # clean word boundary
    return truncated + "\n\n[Context truncated for token safety]"


def _build_rag_context(hits: list[dict]) -> tuple[str, list[str]]:
    """Convert VectorStore search results into context string + citations."""
    parts: list[str] = []
    citations: list[str] = []
    for h in hits:
        parts.append(h["text"])
        src = h.get("metadata", {}).get("source", "unknown")
        if src not in citations:
            citations.append(src)
    context = "\n---\n".join(parts)
    return _truncate_context(context), citations


# ─── Pipeline ─────────────────────────────────────────────────────────────────

async def run_pipeline(
    query: str,
    role: str,
    user_id: str | None = None,
    department: str | None = None,
) -> PipelineResult:
    """
    Execute the full query pipeline and return a PipelineResult.

    Stages
    ------
    1. Guardrail validation
    2. Emergency triage
    3. Intent classification  (ERP → DB  |  Knowledge → FAISS  |  General → LLM)
    4. Context assembly (token-limited)
    5. LLaMA inference (timeout-protected)
    6. PHI redaction
    7. Audit logging
    """
    t0 = time.perf_counter()
    result = PipelineResult(query=query)

    # ── 1. Guardrail Validation ──────────────────────────────────────────
    try:
        GuardrailService.validate_prompt(query)
    except Exception as e:
        logger.warning("Pipeline: guardrail blocked query: %s", e)
        result.status = "blocked"
        result.response = "Your query was blocked by safety filters. Please rephrase."
        result.query_type = QueryType.FALLBACK
        result.response_time_ms = _elapsed_ms(t0)
        return result

    # Scrub accidental PHI from the query itself
    query = PHIScrubber.redact(query)
    result.query = query

    # ── 2. Emergency Triage ──────────────────────────────────────────────
    severity, symptoms = EmergencyDetector.analyze_query(query)
    if severity == Severity.CRITICAL:
        NotificationService.trigger_emergency_alert(
            {"sub": user_id, "role": role}, symptoms, query
        )
        result.response = EmergencyDetector.get_emergency_advice(symptoms)
        result.query_type = QueryType.EMERGENCY
        result.status = "EMERGENCY_OVERRIDE"
        result.response_time_ms = _elapsed_ms(t0)
        _log_pipeline(result)
        return result

    # ── 3. Intent Classification ─────────────────────────────────────────
    context_text = ""
    citations: list[str] = []

    # 3a. Try ERP structured query first
    try:
        handled, struct_ctx = await asyncio.wait_for(
            asyncio.to_thread(try_structured_query, query, role, user_id),
            timeout=RETRIEVAL_TIMEOUT,
        )
    except asyncio.TimeoutError:
        handled, struct_ctx = False, ""
        logger.warning("Pipeline: ERP query timed out.")
    except Exception as e:
        handled, struct_ctx = False, ""
        logger.error("Pipeline: ERP query error: %s", e)

    if handled:
        result.query_type = QueryType.ERP
        result.erp_used = True
        context_text = _truncate_context(struct_ctx)
    else:
        # 3b. FAISS knowledge retrieval
        try:
            hits = await asyncio.wait_for(
                asyncio.to_thread(VectorStore.search, query, FAISS_TOP_K),
                timeout=RETRIEVAL_TIMEOUT,
            )
        except asyncio.TimeoutError:
            hits = []
            logger.warning("Pipeline: FAISS search timed out.")
        except Exception as e:
            hits = []
            logger.error("Pipeline: FAISS search error: %s", e)

        if hits and hits[0].get("score", 0) > 0.25:      # relevance threshold
            result.query_type = QueryType.KNOWLEDGE
            result.vector_hits = len(hits)
            context_text, citations = _build_rag_context(hits)
        else:
            result.query_type = QueryType.GENERAL
            result.vector_hits = 0

    # ── 4. LLaMA Inference (timeout-protected) ───────────────────────────
    try:
        llm_response = await asyncio.wait_for(
            asyncio.to_thread(
                LlamaService.generate_response,
                prompt=query,
                context=context_text,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            ),
            timeout=LLM_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Pipeline: LLaMA inference timed out after %.0f s", LLM_TIMEOUT)
        result.response = (
            "The AI model is taking too long to respond. "
            "Please try again or consult your physician directly."
        )
        result.status = "timeout"
        result.query_type = QueryType.FALLBACK
        result.response_time_ms = _elapsed_ms(t0)
        _log_pipeline(result)
        return result
    except Exception as e:
        logger.error("Pipeline: LLaMA inference failed: %s", e)
        result.response = "An internal error occurred. Please try again later."
        result.status = "error"
        result.error = str(e)
        result.query_type = QueryType.FALLBACK
        result.response_time_ms = _elapsed_ms(t0)
        _log_pipeline(result)
        return result

    # ── 5. PHI Redaction on Output ───────────────────────────────────────
    result.response = PHIScrubber.redact(llm_response)
    result.citations = citations
    result.response_time_ms = _elapsed_ms(t0)

    # ── 6. Audit Log ─────────────────────────────────────────────────────
    _log_pipeline(result)

    return result


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _elapsed_ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def _log_pipeline(r: PipelineResult) -> None:
    logger.info(
        "PIPELINE  type=%s  erp=%s  vectors=%d  time=%.0fms  status=%s  query=%.60s",
        r.query_type.value,
        r.erp_used,
        r.vector_hits,
        r.response_time_ms,
        r.status,
        r.query,
    )
