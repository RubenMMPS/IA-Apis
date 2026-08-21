from app.agents.tools.base import Tool
from app.llm.models import ToolDefinition, ToolParameter
from app.embeddings.base import EmbeddingProvider
from app.embeddings.models import EmbeddingRequest
from app.db.session import AsyncSessionLocal
from app.db.repository import search_similar_chunks


class RetrievalTool(Tool):
    def __init__(self, embedding_provider: EmbeddingProvider, top_k: int = 3):
        self._embeddings = embedding_provider
        self._top_k = top_k

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_knowledge_base",
            description=(
                "Busca en la base de conocimiento indexada del equipo "
                "información relevante para la tarea actual."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    description="Términos de búsqueda, en lenguaje natural",
                    type="string",
                )
            ],
        )

    async def execute(self, query: str) -> str:
        query_embedding = await self._embeddings.embed(
            EmbeddingRequest(text=query, task_type="RETRIEVAL_QUERY")
        )

        async with AsyncSessionLocal() as session:
            chunks = await search_similar_chunks(
                session, query_embedding.vector, limit=self._top_k
            )

        if not chunks:
            return "No se encontró información relevante en la base de conocimiento."

        return "\n---\n".join(c.content for c in chunks)