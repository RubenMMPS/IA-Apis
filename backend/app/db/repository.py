from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeChunk


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