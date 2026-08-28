from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.dependencies import get_llm_provider
from app.llm.models import LLMRequest, LLMMessage, LLMResponse
from app.api.routes.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    conn_string = settings.database_url.replace("+asyncpg", "")

    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        yield


app = FastAPI(title="AI Software Engineering Team - Backend", lifespan=lifespan)

app.include_router(tasks_router)


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