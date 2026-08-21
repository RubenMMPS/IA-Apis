from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.plan import Plan, PlanStep


class PlanStepOutput(BaseModel):
    id: str
    description: str


class PlannerOutput(BaseModel):
    steps: list[PlanStepOutput]


class PlannerAgent(BaseAgent):
    name = "planner"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Planner de un equipo de ingeniería de software formado por IA. "
            "Tu única responsabilidad es descomponer la tarea de programación del usuario "
            "en una lista ordenada de pasos claros y accionables para el resto del equipo "
            "(Researcher, Architect, Developer, Tester, Reviewer). "
            "Cada paso debe tener un id corto único y una descripción concisa."
        )

    def build_user_message(self, state: GraphState) -> str:
        return f"Tarea del usuario:\n{state['original_request']}"

    def output_schema(self) -> type[PlannerOutput]:
        return PlannerOutput

    def apply_output(self, state: GraphState, output: PlannerOutput) -> dict:
        plan = Plan(
            steps=[
                PlanStep(id=s.id, description=s.description, status="pending")
                for s in output.steps
            ]
        )
        return {"plan": plan}