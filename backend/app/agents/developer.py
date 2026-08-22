from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.code import CodeArtifacts


class DeveloperAgent(BaseAgent):
    name = "developer"
    max_output_tokens = 4096

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Developer de un equipo de ingeniería de software formado por IA. "
            "Implementa el código Python siguiendo exactamente la especificación técnica "
            "del Architect: los mismos nombres de componentes, la misma estructura de "
            "archivos. Escribe código completo, funcional y con type hints, sin marcadores "
            "de posición ni TODOs. Si recibes feedback de una iteración anterior "
            "(tests fallidos o revisión con cambios solicitados), corrígelo mostrando "
            "el archivo completo actualizado, no solo el fragmento cambiado."
        )

    def build_user_message(self, state: GraphState) -> str:
        spec = state["architecture_spec"]
        decisions_text = "\n".join(f"- {d.component}: {d.description}" for d in spec.decisions)
        files_text = ", ".join(spec.files_to_create)

        parts = [
            f"Especificación técnica:\n{spec.summary}\n\nDecisiones:\n{decisions_text}",
            f"\nArchivos a crear: {files_text}",
        ]

        test_results = state.get("test_results")
        if test_results and not test_results.passed:
            parts.append(f"\nLos tests fallaron en el intento anterior:\n{test_results.details}")

        review_feedback = state.get("review_feedback")
        if review_feedback and review_feedback.decision == "changes_requested":
            parts.append(f"\nEl Reviewer pidió cambios:\n{review_feedback.comments}")

        return "\n".join(parts)

    def output_schema(self) -> type[CodeArtifacts]:
        return CodeArtifacts

    def apply_output(self, state: GraphState, output: CodeArtifacts) -> dict:
        return {"code_artifacts": output}