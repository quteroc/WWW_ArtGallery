"""
Comment model for user artwork comments.
"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    """Comment model linking users to artworks with text content."""
    
    __tablename__ = "comments"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    artwork_id: UUID = Field(foreign_key="artworks.id", index=True)
    content: str = Field(max_length=1000)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": "now()"}
    )
