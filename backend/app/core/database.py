from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings

# Async engine for FastAPI endpoints
engine = create_async_engine(settings.database_url, echo=False, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for background tasks (drift detection, hallucination scoring, alerts)
sync_engine = create_engine(settings.sync_database_url, pool_size=5, max_overflow=5)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db() -> Session:
    return SyncSession()
