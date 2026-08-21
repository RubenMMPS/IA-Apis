from pydantic import BaseModel

class ResearchFindings(BaseModel):
    summary: str
    key_points: list[str]