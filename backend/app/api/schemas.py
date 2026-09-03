import uuid
from datetime import datetime
from pydantic import BaseModel

from app.db.models import TaskStatus


class CreateTaskRequest(BaseModel):
    original_request: str


class TaskResponse(BaseModel):
    id: uuid.UUID
    status: TaskStatus
    original_request: str
    result_summary: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CodeFileResponse(BaseModel):
    filename: str
    content: str


class CodeArtifactsResponse(BaseModel):
    files: list[CodeFileResponse]
    notes: str

class TestResultResponse(BaseModel):
    passed: bool
    exit_code: int
    output: str