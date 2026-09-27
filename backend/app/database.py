"""
Database setup using SQLAlchemy async with SQLite.
Swappable to PostgreSQL by changing DATABASE_URL.
"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Ensure data directory exists
db_path = Path(__file__).parent.parent / "data"
db_path.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Database initialization is now managed by Alembic."""
    pass


async def get_db() -> AsyncSession:
    """Dependency for FastAPI endpoints."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
