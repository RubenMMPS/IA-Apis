from functools import lru_cache
from app.embeddings.base import EmbeddingProvider
from app.embeddings.config import EmbeddingSettings
from app.embeddings.factory import create_embedding_provider

@lru_cache
def get_embedding_settings() -> EmbeddingSettings:
    return EmbeddingSettings()

@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return create_embedding_provider(get_embedding_settings())