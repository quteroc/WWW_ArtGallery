"""
Database initialization utilities.
"""
from sqlmodel import SQLModel
from app.db.session import engine
from app.models.user import User
from app.models.category import Category
from app.models.artwork import Artwork


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
