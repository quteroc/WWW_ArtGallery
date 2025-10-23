"""
Database session management with async SQLAlchemy.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Default echo to False; allow override via env var SQL_ECHO=true
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=SQL_ECHO,
    future=True,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """Dependency for FastAPI routes to get database session."""
    async with async_session() as session:
        yield session
