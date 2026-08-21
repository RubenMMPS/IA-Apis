from app.embeddings.base import EmbeddingProvider
from app.embeddings.config import EmbeddingSettings
from app.embeddings.providers.gemini import GeminiEmbeddingProvider

def create_embedding_provider(settings: EmbeddingSettings) -> EmbeddingProvider:
    if settings.provider == "gemini":
        return GeminiEmbeddingProvider(api_key=settings.api_key, model_name=settings.model_name)
    raise ValueError(f"Proveedor de embeddings desconocido: {settings.provider}")