from pydantic import BaseModel
from typing import Literal

class PlanStep(BaseModel):
    id: str
    description: str
    status: Literal["pending", "in_progress", "done", "failed"] = "pending"

class Plan(BaseModel):
    steps: list[PlanStep] = []