from pydantic import BaseModel
from typing import Literal

from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.review import ReviewFeedback
from app.agents.constraint_checks import check_constraints_violations


class ReviewerLLMOutput(BaseModel):
    decision: Literal["approved", "changes_requested"]
    comments: str
    constraints_violated: list[str] = []


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
            "de calidad o de correctitud, no por preferencias de estilo menores. "
            "\n\nADEMÁS, si se indican restricciones técnicas obligatorias de la tarea, "
            "debes comprobar explícitamente si el código las cumple. Si detectas alguna "
            "restricción incumplida (por ejemplo, uso de una tecnología prohibida), "
            "añádela literalmente a 'constraints_violated' y la decisión debe ser "
            "'changes_requested' obligatoriamente, incluso si el resto del código es "
            "correcto — el incumplimiento de una restricción explícita del usuario "
            "siempre invalida la aprobación. Si no hay restricciones o todas se cumplen, "
            "deja 'constraints_violated' como lista vacía."
        )

    def build_user_message(self, state: GraphState) -> str:
        code = state["code_artifacts"]
        files_text = "\n\n".join(f"--- {f.filename} ---\n{f.content}" for f in code.files)

        test_results = state.get("test_results")
        tests_text = "Pasaron correctamente." if test_results and test_results.passed else "No disponibles."

        parts = [f"Código a revisar:\n{files_text}\n\nEstado de los tests: {tests_text}"]

        plan = state.get("plan")
        if plan and plan.constraints:
            constraints_text = "\n".join(f"- {c}" for c in plan.constraints)
            parts.append(f"\nRESTRICCIONES OBLIGATORIAS a verificar en el código:\n{constraints_text}")

        return "\n".join(parts)

    def output_schema(self) -> type[ReviewerLLMOutput]:
        return ReviewerLLMOutput

    def apply_output(self, state: GraphState, output: ReviewerLLMOutput) -> dict:
            plan = state.get("plan")
            constraints = plan.constraints if plan else []
            code = state["code_artifacts"]

            auto_violations = check_constraints_violations(constraints, code.files)
            all_violations = list(output.constraints_violated) + [
                v for v in auto_violations if v not in output.constraints_violated
            ]

            decision = output.decision
            if all_violations:
                decision = "changes_requested"

            feedback = ReviewFeedback(
                decision=decision,
                comments=output.comments,
                constraints_violated=all_violations,
            )
            return {"review_feedback": feedback}