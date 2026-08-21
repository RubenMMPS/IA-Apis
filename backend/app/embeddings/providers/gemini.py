from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.embeddings.base import EmbeddingProvider
from app.embeddings.models import EmbeddingRequest, EmbeddingResponse
from app.llm.exceptions import LLMProviderError  # reutilizamos la misma jerarquía de errores

EMBEDDING_DIM = 768


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-embedding-001"):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        try:
            result = await self._client.aio.models.embed_content(
                model=self._model_name,
                contents=request.text,
                config=types.EmbedContentConfig(
                    task_type=request.task_type,
                    output_dimensionality=EMBEDDING_DIM,
                ),
            )
        except APIError as e:
            raise LLMProviderError(f"Error del proveedor de embeddings Gemini: {e}") from e

        vector = result.embeddings[0].values
        return EmbeddingResponse(vector=vector, dimensions=len(vector))