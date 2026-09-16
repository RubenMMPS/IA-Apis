from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from app.core.config import get_settings
from app.api.routes.tasks import router as tasks_router

ALLOWED_STATE_TYPES = [
    ("app.graph.state.plan", "Plan"),
    ("app.graph.state.messages", "AgentMessage"),
    ("app.graph.state.test_result", "TestResult"),
    ("app.graph.state.code", "CodeArtifacts"),
    ("app.graph.state.review", "ReviewFeedback"),
    ("app.graph.state.architecture", "ArchitectureSpec"),
    ("app.graph.state.research", "ResearchFindings"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    conn_string = settings.database_url.replace("+asyncpg", "")
    serde = JsonPlusSerializer(allowed_msgpack_modules=ALLOWED_STATE_TYPES)

    async with AsyncPostgresSaver.from_conn_string(conn_string, serde=serde) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        yield


app = FastAPI(title="AI Software Engineering Team - Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)


@app.get("/health")
async def health():
    return {"status": "ok"}