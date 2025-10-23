"""
User model for authentication and authorization.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model with roles (user, manager, admin)."""
    
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="user")  # user, manager, admin
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
