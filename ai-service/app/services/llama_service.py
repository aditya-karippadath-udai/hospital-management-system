import os
import time
import logging
import psutil
from llama_cpp import Llama

logger = logging.getLogger(__name__)

# Absolute path to the GGUF model
DEFAULT_MODEL_PATH = r"F:\Practice\python\hospital-management-system\ai-service\Lama\llama\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"


class LlamaService:
    """
    Singleton wrapper around llama-cpp-python.
    Loads GGUF model once at startup, reuses for all inference.
    """

    _instance: "LlamaService | None" = None
    _model: Llama | None = None

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self):
        raise RuntimeError("Use LlamaService.initialize() instead")

    @classmethod
    def initialize(
        cls,
        model_path: str = DEFAULT_MODEL_PATH,
        n_gpu_layers: int = -1,       # -1 = offload all layers to GPU
        n_ctx: int = 4096,            # context window
        n_batch: int = 512,
        verbose: bool = False,
    ) -> None:
        """Load the model into memory. Call once at app startup."""

        if cls._model is not None:
            logger.info("LlamaService: model already loaded – skipping.")
            return

        # Fail-fast guard
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"GGUF model not found at: {model_path}. "
                "Set the MODEL_PATH env var or verify the file exists."
            )

        logger.info("LlamaService: loading model from %s …", model_path)
        mem_before = psutil.Process().memory_info().rss / (1024 ** 2)
        t0 = time.perf_counter()

        cls._model = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            n_batch=n_batch,
            verbose=verbose,
        )

        elapsed = time.perf_counter() - t0
        mem_after = psutil.Process().memory_info().rss / (1024 ** 2)

        logger.info(
            "LlamaService: model loaded in %.2f s  |  RAM delta: +%.0f MB  (total %.0f MB)",
            elapsed,
            mem_after - mem_before,
            mem_after,
        )

        cls._instance = object.__new__(cls)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    @classmethod
    def generate_response(
        cls,
        prompt: str,
        context: str = "",
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        stream: bool = False,
    ):
        """
        Generate a completion from the local LLaMA model.

        Parameters
        ----------
        prompt : str
            The user/system prompt (already assembled by PromptGenerator).
        context : str
            Retrieved RAG context to prepend.
        max_tokens : int
            Hard cap on generated tokens.
        temperature : float
            Sampling temperature (lower = more deterministic).
        stream : bool
            If True, returns a generator yielding token strings.
        """
        if cls._model is None:
            raise RuntimeError(
                "LlamaService not initialized. Call LlamaService.initialize() first."
            )

        # Assemble the full instruction prompt (Llama-3-Instruct chat format)
        system_msg = (
            "You are a medically trained AI assistant integrated into a Hospital ERP. "
            "Answer ONLY using the provided clinical context. "
            "If you are unsure, say so. Never fabricate information."
        )

        full_prompt = (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_msg}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n"
            f"### Clinical Context\n{context}\n\n"
            f"### Query\n{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        if stop is None:
            stop = ["<|eot_id|>", "<|end_of_text|>"]

        t0 = time.perf_counter()

        if stream:
            return cls._stream_generate(full_prompt, max_tokens, temperature, top_p, stop)

        output = cls._model(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            echo=False,
        )

        elapsed = time.perf_counter() - t0
        text = output["choices"][0]["text"].strip()
        tokens_generated = output["usage"]["completion_tokens"]

        logger.info(
            "LlamaService: generated %d tokens in %.2f s (%.1f tok/s)",
            tokens_generated,
            elapsed,
            tokens_generated / elapsed if elapsed > 0 else 0,
        )

        return text

    @classmethod
    def _stream_generate(cls, full_prompt, max_tokens, temperature, top_p, stop):
        """Yield tokens one-by-one for streaming responses."""
        for chunk in cls._model(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            echo=False,
            stream=True,
        ):
            token_text = chunk["choices"][0]["text"]
            if token_text:
                yield token_text

    # ------------------------------------------------------------------
    # Health & Memory
    # ------------------------------------------------------------------
    MEMORY_CAP_MB = int(os.getenv("LLM_MEMORY_CAP_MB", "8192"))  # default 8 GB

    @classmethod
    def is_ready(cls) -> bool:
        return cls._model is not None

    @classmethod
    def memory_usage_mb(cls) -> float:
        """Current process RSS in MB."""
        return psutil.Process().memory_info().rss / (1024 ** 2)

    @classmethod
    def check_memory_cap(cls) -> bool:
        """Return True if memory is within cap, False if exceeded."""
        usage = cls.memory_usage_mb()
        if usage > cls.MEMORY_CAP_MB:
            logger.warning(
                "LlamaService: memory cap exceeded (%.0f / %d MB)",
                usage, cls.MEMORY_CAP_MB,
            )
            return False
        return True

    @classmethod
    def get_health_info(cls) -> dict:
        """Structured health snapshot for /health/ai."""
        mem = cls.memory_usage_mb()
        return {
            "model_loaded": cls.is_ready(),
            "memory_usage_mb": round(mem, 1),
            "memory_cap_mb": cls.MEMORY_CAP_MB,
            "memory_ok": mem <= cls.MEMORY_CAP_MB,
        }
