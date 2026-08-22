from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.architecture import ArchitectureSpec


class ArchitectAgent(BaseAgent):
    name = "architect"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Architect de un equipo de ingeniería de software formado por IA. "
            "A partir del plan y los hallazgos del Researcher, define la especificación "
            "técnica: qué componentes/funciones crear, decisiones de diseño clave "
            "(con su justificación breve) y qué archivos deberá crear el Developer. "
            "Sé concreto y accionable, no genérico."
        )

    def build_user_message(self, state: GraphState) -> str:
        plan = state.get("plan")
        steps_text = "\n".join(f"- {s.description}" for s in plan.steps) if plan else "(sin plan)"

        findings = state.get("research_findings")
        research_text = findings.summary if findings else "(sin research)"

        return (
            f"Tarea original:\n{state['original_request']}\n\n"
            f"Plan:\n{steps_text}\n\n"
            f"Hallazgos del Researcher:\n{research_text}"
        )

    def output_schema(self) -> type[ArchitectureSpec]:
        return ArchitectureSpec

    def apply_output(self, state: GraphState, output: ArchitectureSpec) -> dict:
        return {"architecture_spec": output}