from pydantic import BaseModel

class EmbeddingRequest(BaseModel):
    text: str
    task_type: str = "RETRIEVAL_DOCUMENT"  # o "RETRIEVAL_QUERY" al buscar

class EmbeddingResponse(BaseModel):
    vector: list[float]
    dimensions: int