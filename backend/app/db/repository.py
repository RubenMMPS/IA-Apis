from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.db.models import KnowledgeChunk, Task, TaskStatus, TaskEventRecord
from datetime import datetime


async def insert_chunk(
    session: AsyncSession, content: str, embedding: list[float], metadata: dict | None = None
) -> KnowledgeChunk:
    chunk = KnowledgeChunk(content=content, embedding=embedding, chunk_metadata=metadata or {})
    session.add(chunk)
    await session.commit()
    await session.refresh(chunk)
    return chunk


async def search_similar_chunks(
    session: AsyncSession, query_embedding: list[float], limit: int = 3
) -> list[KnowledgeChunk]:
    stmt = (
        select(KnowledgeChunk)
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def create_task(session: AsyncSession, original_request: str) -> Task:
    task = Task(original_request=original_request, status=TaskStatus.queued)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: uuid.UUID) -> Task | None:
    return await session.get(Task, task_id)


async def update_task_status(
    session: AsyncSession,
    task_id: uuid.UUID,
    status: TaskStatus,
    result_summary: str | None = None,
    error_message: str | None = None,
    total_tokens: int | None = None,
    estimated_cost_usd: float | None = None,
) -> None:
    task = await session.get(Task, task_id)
    if task is None:
        return
    task.status = status
    if result_summary is not None:
        task.result_summary = result_summary
    if error_message is not None:
        task.error_message = error_message
    if total_tokens is not None:
        task.total_tokens = total_tokens
    if estimated_cost_usd is not None:
        task.estimated_cost_usd = estimated_cost_usd
    await session.commit()

async def insert_task_event(
    session: AsyncSession, task_id: str, event_type: str, agent: str | None,
    message: str, timestamp: datetime,
) -> None:
    record = TaskEventRecord(
        task_id=task_id, event_type=event_type, agent=agent,
        message=message, timestamp=timestamp,
    )
    session.add(record)
    await session.commit()


async def get_task_events(session: AsyncSession, task_id: str) -> list[TaskEventRecord]:
    stmt = (
        select(TaskEventRecord)
        .where(TaskEventRecord.task_id == task_id)
        .order_by(TaskEventRecord.timestamp)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())