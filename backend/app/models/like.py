"""
Like model for user artwork likes/favorites.
"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, UniqueConstraint


class Like(SQLModel, table=True):
    """Like/favorite model linking users to artworks."""
    
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("user_id", "artwork_id", name="unique_user_artwork_like"),
    )
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    artwork_id: UUID = Field(foreign_key="artworks.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
