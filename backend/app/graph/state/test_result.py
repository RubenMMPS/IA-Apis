from pydantic import BaseModel

class TestResult(BaseModel):
    passed: bool
    exit_code: int
    output: str