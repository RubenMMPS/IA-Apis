from pydantic import BaseModel

class CodeFile(BaseModel):
    filename: str
    content: str

class CodeArtifacts(BaseModel):
    files: list[CodeFile]
    notes: str  # explicación breve de decisiones tomadas al implementar