import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.repository import create_task, get_task
from app.core.task_executor import InProcessExecutor
from app.api.schemas import CreateTaskRequest, TaskResponse, CodeArtifactsResponse, TestResultResponse
import json
from fastapi.responses import StreamingResponse
from app.core.events import event_bus
from app.graph.build_graph import build_graph
from app.llm.dependencies import get_llm_provider
from app.embeddings.dependencies import get_embedding_provider

router = APIRouter(prefix="/tasks", tags=["tasks"])

async def _sse_generator(task_id: str):
    async for event in event_bus.subscribe(task_id):
        payload = event.model_dump_json()
        yield f"event: {event.event_type}\ndata: {payload}\n\n"


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task_endpoint(
    body: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    task = await create_task(session, body.original_request)

    executor = InProcessExecutor(background_tasks, request.app.state.checkpointer)
    executor.submit(task.id)

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    task = await get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task no encontrada")
    return TaskResponse.model_validate(task)

@router.get("/{task_id}/events")
async def stream_task_events(task_id: uuid.UUID):
    return StreamingResponse(
        _sse_generator(str(task_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/{task_id}/code", response_model=CodeArtifactsResponse)
async def get_task_code(task_id: uuid.UUID, request: Request):
    checkpointer = request.app.state.checkpointer
    graph = build_graph(get_llm_provider(), get_embedding_provider(), checkpointer)
    config = {"configurable": {"thread_id": str(task_id)}}

    snapshot = await graph.aget_state(config)
    code = snapshot.values.get("code_artifacts")

    if code is None:
        raise HTTPException(status_code=404, detail="No hay código generado para esta tarea (aún en curso o sin llegar a Developer)")

    return CodeArtifactsResponse.model_validate(code.model_dump())

@router.get("/{task_id}/test-result", response_model=TestResultResponse)
async def get_task_test_result(task_id: uuid.UUID, request: Request):
    checkpointer = request.app.state.checkpointer
    graph = build_graph(get_llm_provider(), get_embedding_provider(), checkpointer)
    config = {"configurable": {"thread_id": str(task_id)}}

    snapshot = await graph.aget_state(config)
    result = snapshot.values.get("test_results")

    if result is None:
        raise HTTPException(status_code=404, detail="No hay resultados de tests para esta tarea")

    return TestResultResponse.model_validate(result.model_dump())