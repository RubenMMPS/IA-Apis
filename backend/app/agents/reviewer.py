from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.review import ReviewFeedback


class ReviewerAgent(BaseAgent):
    name = "reviewer"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Reviewer de un equipo de ingeniería de software formado por IA. "
            "Revisa el código final del Developer, que ya ha pasado los tests automatizados. "
            "Evalúa legibilidad, adherencia a la especificación del Architect, manejo de "
            "errores y buenas prácticas generales. "
            "Aprueba (approved) si el código es aceptable para entrega, aunque no sea "
            "perfecto. Solo pide cambios (changes_requested) si hay un problema real "
            "de calidad o de correctitud, no por preferencias de estilo menores."
        )

    def build_user_message(self, state: GraphState) -> str:
        code = state["code_artifacts"]
        files_text = "\n\n".join(f"--- {f.filename} ---\n{f.content}" for f in code.files)

        test_results = state.get("test_results")
        tests_text = "Pasaron correctamente." if test_results and test_results.passed else "No disponibles."

        return f"Código a revisar:\n{files_text}\n\nEstado de los tests: {tests_text}"

    def output_schema(self) -> type[ReviewFeedback]:
        return ReviewFeedback

    def apply_output(self, state: GraphState, output: ReviewFeedback) -> dict:
        return {"review_feedback": output}