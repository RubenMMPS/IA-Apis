from app.agents.base import BaseAgent
from app.agents.tools.retrieval import RetrievalTool
from app.graph.state.graph_state import GraphState
from app.graph.state.research import ResearchFindings
from app.embeddings.base import EmbeddingProvider
from app.llm.base import LLMProvider


class ResearcherAgent(BaseAgent):
    name = "researcher"

    def __init__(self, llm: LLMProvider, embedding_provider: EmbeddingProvider):
        super().__init__(llm)
        retrieval_tool = RetrievalTool(embedding_provider=embedding_provider)
        self.tools = [retrieval_tool.definition]
        self.tool_registry = {retrieval_tool.definition.name: retrieval_tool}

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Researcher de un equipo de ingeniería de software formado por IA. "
            "Tu responsabilidad es investigar el plan de trabajo usando la tool "
            "search_knowledge_base para encontrar información relevante ya indexada, "
            "y resumir los hallazgos en un resumen claro y una lista de puntos clave "
            "que ayuden al Architect a diseñar la solución. "
            "Si la tool no devuelve información relevante, indícalo honestamente "
            "en el resumen en vez de inventar contenido."
        )

    def build_user_message(self, state: GraphState) -> str:
        plan = state.get("plan")
        steps_text = "\n".join(f"- {s.description}" for s in plan.steps) if plan else "(sin plan)"
        return (
            f"Tarea original:\n{state['original_request']}\n\n"
            f"Plan a investigar:\n{steps_text}"
        )

    def output_schema(self) -> type[ResearchFindings]:
        return ResearchFindings

    def apply_output(self, state: GraphState, output: ResearchFindings) -> dict:
        return {"research_findings": output}