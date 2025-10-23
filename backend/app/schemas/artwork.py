"""
Artwork schemas for API requests and responses.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ArtworkCreate(BaseModel):
    """Schema for creating an artwork."""
    title: str
    artist: str
    year: Optional[int] = None
    style: str
    image_path: str
    popularity_score: float = 0.0
    is_active: bool = True


class ArtworkUpdate(BaseModel):
    """Schema for updating an artwork (all fields optional)."""
    title: Optional[str] = None
    artist: Optional[str] = None
    year: Optional[int] = None
    style: Optional[str] = None
    image_path: Optional[str] = None
    popularity_score: Optional[float] = None
    is_active: Optional[bool] = None


class ArtworkImport(BaseModel):
    """Schema for importing artwork from file path."""
    image_path: str = Field(..., description="Path like ml/input/wikiart/Baroque/filename.jpg")
    title: Optional[str] = None
    artist: Optional[str] = None
    style: Optional[str] = None
