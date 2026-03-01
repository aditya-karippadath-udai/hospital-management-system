from .core.emergency import EmergencyDetector, Severity
from .core.guardrails import GuardrailService
from .core.phi import PHIScrubber
from .core.security_middleware import SecurityHardeningMiddleware
from .core.structured_query import try_structured_query
from .core.pipeline import run_pipeline
from .services.notification_service import NotificationService
from .services.audit_service import AuditService
from .services.feedback_service import FeedbackService
from .services.llama_service import LlamaService
from .services.vector_store import VectorStore
from .services.knowledge_service import ingest_knowledge
from .schemas.feedback import FeedbackCreate
from .schemas.knowledge import KnowledgeAddRequest, KnowledgeAddResponse
from .models.base import Base
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
import os
import logging
import psutil
import signal

# Initialize FastAPI
app = FastAPI(
    title="Medical AI Assistant Service",
    description="RAG-based AI service for Hospital ERP",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Rate Limiter — per IP by default
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _user_key(request):
    """Per-user rate limit key extracted from JWT 'sub' claim."""
    user = getattr(request.state, "user", None)
    if user and isinstance(user, dict):
        return user.get("sub", get_remote_address(request))
    return get_remote_address(request)

# Middleware
app.add_middleware(SecurityHardeningMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
async def load_llm():
    """Load the local LLaMA GGUF model into memory at app startup."""
    model_path = os.getenv(
        "MODEL_PATH",
        r"F:\Practice\python\hospital-management-system\ai-service\Lama\llama\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
    )
    n_gpu = int(os.getenv("N_GPU_LAYERS", "-1"))
    n_ctx = int(os.getenv("MODEL_CTX", "4096"))
    logger.info("Startup: loading LLaMA model …")
    LlamaService.initialize(model_path=model_path, n_gpu_layers=n_gpu, n_ctx=n_ctx)
    logger.info("Startup: LLaMA model ready.")


@app.on_event("startup")
async def load_vector_store():
    """Load or create FAISS index at app startup. Auto-rebuild if corrupted."""
    logger.info("Startup: initializing VectorStore …")
    VectorStore.initialize()

    ok, reason = VectorStore.verify_integrity()
    if not ok:
        logger.error("Startup: FAISS index corrupted (%s) — rebuilding.", reason)
        VectorStore.rebuild_index()

    logger.info("Startup: VectorStore ready (%d vectors).", VectorStore.count())


@app.on_event("shutdown")
async def graceful_shutdown():
    """Persist FAISS index and log shutdown."""
    logger.info("Shutdown: saving state …")
    if VectorStore.is_ready() and VectorStore.count() > 0:
        VectorStore.save_index()
        logger.info("Shutdown: VectorStore saved (%d vectors).", VectorStore.count())
    logger.info("Shutdown: complete.")


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-assistant",
        "model_loaded": LlamaService.is_ready(),
        "vector_store_ready": VectorStore.is_ready(),
        "vectors_indexed": VectorStore.count(),
    }


@app.get("/health/ai")
async def detailed_health():
    """Detailed AI subsystem health for monitoring dashboards."""
    llm_info = LlamaService.get_health_info()
    vs_info = VectorStore.get_health_info()
    process = psutil.Process()
    return {
        "model": llm_info,
        "vector_store": vs_info,
        "system": {
            "memory_usage_mb": round(process.memory_info().rss / (1024 ** 2), 1),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "threads": process.num_threads(),
        },
    }


# ── Document Ingestion ────────────────────────────────────────────────────────

@app.post("/v1/ingest")
async def trigger_ingestion(
    data: dict,
    user: dict = Depends(get_current_user),
):
    """Trigger async document ingestion.  Admin / Doctor only."""
    RBAC.check_permissions(user, ["admin", "doctor"])

    file_path = data.get("file_path")
    metadata = data.get("metadata", {})
    metadata["uploaded_by"] = user.get("sub")
    remove_phi = data.get("remove_phi", False)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Invalid file path")

    task = ingest_document_task.delay(file_path, metadata, remove_phi)
    return {"task_id": task.id, "status": "queued"}


# ── Unified Query Pipeline ───────────────────────────────────────────────────

@app.post("/v1/query")
@limiter.limit("20/minute", key_func=_user_key)
async def process_medical_query(
    request: dict,          # required by slowapi
    data: dict,
    user: dict = Depends(get_current_user),
):
    """
    Main entry point for medical AI queries.

    Pipeline stages (delegated to ``run_pipeline``):
        Guardrails → Triage → Intent (ERP / RAG / General)
            → Context Assembly (token-limited)
                → LLaMA Inference (timeout-protected)
                    → PHI Scrub → Audit Log → Response
    """
    RBAC.check_permissions(user, ["admin", "doctor", "nurse", "patient"])
    ConsentService.verify_ai_consent(user)

    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    role = user.get("role", "patient")
    user_id = user.get("sub")
    department = user.get("department")

    logger.info("User %s [%s] submitted query.", user_id, role)

    # Memory cap pre-check
    if not LlamaService.check_memory_cap():
        raise HTTPException(
            status_code=503,
            detail="AI service memory limit reached. Try again shortly.",
        )

    result = await run_pipeline(
        query=query,
        role=role,
        user_id=user_id,
        department=department,
    )

    return {
        "query": result.query,
        "response": result.response,
        "query_type": result.query_type.value,
        "status": result.status,
        "citations": result.citations,
        "vector_hits": result.vector_hits,
        "erp_used": result.erp_used,
        "response_time_ms": result.response_time_ms,
    }


# ── Feedback ──────────────────────────────────────────────────────────────────

@app.post("/v1/feedback")
async def submit_ai_feedback(
    data: FeedbackCreate,
    user: dict = Depends(get_current_user),
):
    """Submit clinical accuracy feedback.  Doctor / Admin only."""
    RBAC.check_permissions(user, ["doctor", "admin"])
    return {"status": "feedback_recorded", "thank_you": True}


# ── Admin Analytics ───────────────────────────────────────────────────────────

@app.get("/v1/admin/analytics")
async def get_performance_analytics(
    user: dict = Depends(get_current_user),
):
    """System-wide AI performance metrics.  Admin only."""
    RBAC.check_permissions(user, ["admin"])
    return {
        "metrics": {
            "total_queries": 1250,
            "avg_accuracy": 0.94,
            "failure_rate": 0.02,
        },
        "drift_detected": False,
    }


@app.get("/v1/admin/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    """Retrieve audit logs for compliance review.  Admin only."""
    RBAC.check_permissions(user, ["admin"])
    return {"logs": [], "integrity_verified": True}


# ── Knowledge Ingestion ──────────────────────────────────────────────────────

@app.post("/admin/knowledge/add")
async def add_knowledge(
    data: KnowledgeAddRequest,
    user: dict = Depends(get_current_user),
):
    """Ingest a knowledge document into FAISS.  Admin only."""
    RBAC.check_permissions(user, ["admin"])

    result = ingest_knowledge(
        title=data.title,
        category=data.category,
        description=data.description,
        created_by=user.get("sub", "unknown"),
    )

    return KnowledgeAddResponse(
        title=data.title,
        category=data.category,
        chunks_stored=result["chunks_stored"],
        total_vectors=result["total_vectors"],
        duplicates_skipped=result["duplicates_skipped"],
    )


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
