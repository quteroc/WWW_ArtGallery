"""
Artwork model for storing art pieces.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class Artwork(SQLModel, table=True):
    """Artwork model with metadata and relationships."""
    
    __tablename__ = "artworks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True)
    artist: str = Field(index=True)
    year: Optional[int] = None
    style: str = Field(foreign_key="categories.name")
    image_path: str  # relative path: "ml/input/wikiart/Baroque/filename.jpg"
    image_url: str  # served URL: "/static/artworks/Baroque/filename.jpg"
    popularity_score: float = Field(default=0.0, index=True)
    views: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
