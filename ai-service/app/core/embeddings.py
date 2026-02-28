import os
import hashlib
import json
import redis
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import requests

logger = logging.getLogger(__name__)

class EmbeddingProvider(ABC):
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._version = "v1"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts).tolist()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def version(self) -> str:
        return self._version

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        self._api_key = api_key
        self._model_name = model_name
        self._version = "v1"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Mocking for now, in prod replace with actual openai-python client
        logger.info(f"Calling OpenAI API for {len(texts)} embeddings...")
        return [[0.1] * 1536 for _ in texts] # Mock 1536 dim

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def version(self) -> str:
        return self._version

class EmbeddingService:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/1"))
        
        # Priority: OpenAI -> Local Fallback
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.provider = OpenAIEmbeddingProvider(api_key)
            self.fallback_provider = LocalEmbeddingProvider()
        else:
            self.provider = LocalEmbeddingProvider()
            self.fallback_provider = None

    def _get_cache_key(self, text: str, provider_name: str, version: str) -> str:
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"emb:{provider_name}:{version}:{text_hash}"

    def get_embeddings(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        results = [None] * len(texts)
        missing_indices = []
        
        if use_cache:
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text, self.provider.model_name, self.provider.version)
                cached = self.redis_client.get(cache_key)
                if cached:
                    results[i] = json.loads(cached)
                else:
                    missing_indices.append(i)
        else:
            missing_indices = list(range(len(texts)))

        if missing_indices:
            missing_texts = [texts[i] for i in missing_indices]
            try:
                new_embeddings = self.provider.get_embeddings(missing_texts)
            except Exception as e:
                logger.error(f"Primary embedding provider failed: {e}")
                if self.fallback_provider:
                    logger.info("Falling back to local embeddings...")
                    new_embeddings = self.fallback_provider.get_embeddings(missing_texts)
                else:
                    raise

            # Cache and fill results
            for i, original_index in enumerate(missing_indices):
                emb = new_embeddings[i]
                results[original_index] = emb
                if use_cache:
                    cache_key = self._get_cache_key(texts[original_index], self.provider.model_name, self.provider.version)
                    self.redis_client.setex(cache_key, 86400 * 30, json.dumps(emb)) # 30 days cache

        return results
