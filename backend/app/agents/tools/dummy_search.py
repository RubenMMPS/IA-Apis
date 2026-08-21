from app.agents.tools.base import Tool
from app.llm.models import ToolDefinition, ToolParameter

class DummySearchTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_knowledge_base",
            description="Busca información relevante en la base de conocimiento del equipo",
            parameters=[ToolParameter(name="query", description="Términos de búsqueda", type="string")],
        )

    async def execute(self, query: str) -> str:
        return f"[Resultado simulado] No hay conocimiento indexado aún sobre: '{query}'"