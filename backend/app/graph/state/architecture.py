from pydantic import BaseModel

class ArchitectureDecision(BaseModel):
    component: str
    description: str

class ArchitectureSpec(BaseModel):
    summary: str
    decisions: list[ArchitectureDecision]
    files_to_create: list[str]