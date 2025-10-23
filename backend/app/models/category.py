"""
Category model for art styles/categories.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """Art styles/categories (e.g., Baroque, Renaissance)."""
    
    __tablename__ = "categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)  # e.g., "Baroque", "Renaissance"
    slug: str = Field(unique=True, index=True)
