from abc import ABC, abstractmethod
from app.embeddings.models import EmbeddingRequest, EmbeddingResponse

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...