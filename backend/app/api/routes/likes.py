"""
Likes API endpoints for user artwork favorites.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.like import Like
from app.models.artwork import Artwork
from pydantic import BaseModel

router = APIRouter()


class LikedArtworkResponse(BaseModel):
    """Response model for liked artwork."""
    id: UUID
    title: str
    artist: str
    style: str
    image_url: str


class StyleStatsResponse(BaseModel):
    """Response model for style statistics."""
    style: str
    count: int
    percentage: float


@router.post("/likes/{artwork_id}", status_code=status.HTTP_200_OK)
async def like_artwork(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Like an artwork for the current user.
    
    - **artwork_id**: ID of the artwork to like
    
    Returns 200 with liked=True (created or already liked).
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
    
    # Check if already liked
    like_query = select(Like).where(
        and_(
            Like.user_id == current_user.id,
            Like.artwork_id == artwork_id
        )
    )
    result = await db.execute(like_query)
    existing_like = result.scalar_one_or_none()
    
    if existing_like:
        return {"message": "Artwork already liked", "liked": True}
    
    # Create new like
    new_like = Like(
        user_id=current_user.id,
        artwork_id=artwork_id
    )
    db.add(new_like)
    await db.commit()
    
    return {"message": "Artwork liked successfully", "liked": True}


@router.delete("/likes/{artwork_id}", status_code=status.HTTP_200_OK)
async def unlike_artwork(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unlike an artwork for the current user.
    
    - **artwork_id**: ID of the artwork to unlike
    
    Returns 200 if deleted, 404 if not found.
    """
    # Find the like
    like_query = select(Like).where(
        and_(
            Like.user_id == current_user.id,
            Like.artwork_id == artwork_id
        )
    )
    result = await db.execute(like_query)
    like = result.scalar_one_or_none()
    
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )
    
    await db.delete(like)
    await db.commit()
    
    return {"message": "Artwork unliked successfully", "liked": False}


@router.get("/likes/me", response_model=List[LikedArtworkResponse])
async def get_my_likes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all liked artworks for the current user.
    
    Returns list of liked artworks with basic information.
    """
    # Query likes with artwork join
    query = (
        select(Artwork)
        .join(Like, Like.artwork_id == Artwork.id)
        .where(Like.user_id == current_user.id)
        .order_by(Like.created_at.desc())
    )
    
    result = await db.execute(query)
    artworks = result.scalars().all()
    
    return [
        LikedArtworkResponse(
            id=artwork.id,
            title=artwork.title,
            artist=artwork.artist,
            style=artwork.style,
            image_url=artwork.image_url
        )
        for artwork in artworks
    ]


@router.get("/likes/me/stats", response_model=List[StyleStatsResponse])
async def get_my_likes_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about liked artworks by style.
    
    Returns style distribution with count and percentage.
    """
    # Query to count likes by style
    query = (
        select(
            Artwork.style,
            func.count(Like.id).label('count')
        )
        .join(Like, Like.artwork_id == Artwork.id)
        .where(Like.user_id == current_user.id)
        .group_by(Artwork.style)
        .order_by(func.count(Like.id).desc())
    )
    
    result = await db.execute(query)
    style_counts = result.all()
    
    # Calculate total
    total = sum(count for _, count in style_counts)
    
    if total == 0:
        return []
    
    # Build response with percentages
    return [
        StyleStatsResponse(
            style=style,
            count=count,
            percentage=round((count / total) * 100, 1)
        )
        for style, count in style_counts
    ]


@router.get("/likes/check/{artwork_id}")
async def check_if_liked(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if an artwork is liked by the current user.
    
    - **artwork_id**: ID of the artwork to check
    
    Returns {"liked": true/false}
    """
    like_query = select(Like).where(
        and_(
            Like.user_id == current_user.id,
            Like.artwork_id == artwork_id
        )
    )
    result = await db.execute(like_query)
    like = result.scalar_one_or_none()
    
    return {"liked": like is not None}
