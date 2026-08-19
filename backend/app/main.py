from fastapi import FastAPI, Depends

from app.llm.base import LLMProvider
from app.llm.dependencies import get_llm_provider
from app.llm.models import LLMRequest, LLMMessage, LLMResponse

app = FastAPI(title="AI Software Engineering Team - Backend")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/llm/test", response_model=LLMResponse)
async def test_llm(
    prompt: str,
    provider: LLMProvider = Depends(get_llm_provider),
):
    request = LLMRequest(messages=[LLMMessage(role="user", content=prompt)])
    return await provider.generate(request)