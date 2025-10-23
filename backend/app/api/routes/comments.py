"""
Comments API endpoints for artwork comments.
"""
from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.comment import Comment
from app.models.artwork import Artwork

router = APIRouter()


class CommentCreate(BaseModel):
    """Request model for creating a comment."""
    content: str = Field(..., max_length=1000, min_length=1)


class CommentResponse(BaseModel):
    """Response model for a comment with user info."""
    id: UUID
    user_id: UUID
    artwork_id: UUID
    username: str
    content: str
    created_at: datetime


@router.post("/comments/{artwork_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    artwork_id: UUID,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a comment on an artwork.
    
    - **artwork_id**: ID of the artwork to comment on
    - **content**: Comment text (1-1000 characters)
    
    Requires authentication.
    """
    # Check if artwork exists
    artwork_query = select(Artwork).where(Artwork.id == artwork_id)
    artwork_result = await db.execute(artwork_query)
    artwork = artwork_result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Create new comment
    new_comment = Comment(
        user_id=current_user.id,
        artwork_id=artwork_id,
        content=comment_data.content
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    
    return CommentResponse(
        id=new_comment.id,
        user_id=new_comment.user_id,
        artwork_id=new_comment.artwork_id,
        username=current_user.username,
        content=new_comment.content,
        created_at=new_comment.created_at
    )


@router.get("/comments/{artwork_id}", response_model=List[CommentResponse])
async def get_comments(
    artwork_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all comments for an artwork.
    
    - **artwork_id**: ID of the artwork
    
    Returns comments in descending order (newest first) with username.
    """
    # Query comments with user join
    query = (
        select(Comment, User.username)
        .join(User, User.id == Comment.user_id)
        .where(Comment.artwork_id == artwork_id)
        .order_by(Comment.created_at.desc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            artwork_id=comment.artwork_id,
            username=username,
            content=comment.content,
            created_at=comment.created_at
        )
        for comment, username in rows
    ]


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a comment.
    
    - **comment_id**: ID of the comment to delete
    
    Only the comment author, a manager, or an admin can delete a comment.
    """
    # Find the comment
    comment_query = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(comment_query)
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check authorization: must be comment owner, manager, or admin
    is_owner = comment.user_id == current_user.id
    is_moderator = current_user.role in ["manager", "admin"]
    
    if not (is_owner or is_moderator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    await db.delete(comment)
    await db.commit()
    
    return None
