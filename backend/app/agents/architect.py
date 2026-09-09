from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.architecture import ArchitectureSpec


class ArchitectAgent(BaseAgent):
    name = "architect"

    async def run(self, state: GraphState) -> dict:
        counts = dict(state.get("iteration_counts", {}))
        counts["architect"] = counts.get("architect", 0) + 1

        delta = await super().run(state)
        delta["iteration_counts"] = counts
        delta["architect_last_run_failed"] = "architecture_spec" not in delta
        return delta

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Architect de un equipo de ingeniería de software formado por IA. "
            "A partir del plan y los hallazgos del Researcher, define la especificación "
            "técnica: qué componentes/funciones crear, decisiones de diseño clave "
            "(con su justificación breve) y qué archivos deberá crear el Developer. "
            "Sé concreto y accionable, no genérico. "
            "Si se indican restricciones técnicas obligatorias, tu diseño debe respetarlas "
            "estrictamente — no propongas componentes ni dependencias que las incumplan."
        )

    def build_user_message(self, state: GraphState) -> str:
        plan = state.get("plan")
        steps_text = "\n".join(f"- {s.description}" for s in plan.steps) if plan else "(sin plan)"

        findings = state.get("research_findings")
        research_text = findings.summary if findings else "(sin research)"

        parts = [
            f"Tarea original:\n{state['original_request']}\n\n"
            f"Plan:\n{steps_text}\n\n"
            f"Hallazgos del Researcher:\n{research_text}",
        ]

        if plan and plan.constraints:
            constraints_text = "\n".join(f"- {c}" for c in plan.constraints)
            parts.append(
                f"\nRESTRICCIONES OBLIGATORIAS que la especificación técnica debe respetar:\n{constraints_text}"
            )

        return "\n".join(parts)

    def output_schema(self) -> type[ArchitectureSpec]:
        return ArchitectureSpec

    def apply_output(self, state: GraphState, output: ArchitectureSpec) -> dict:
        return {"architecture_spec": output}