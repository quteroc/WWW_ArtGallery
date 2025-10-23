"""
Web routes for My Likes page.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.api.deps import get_db, get_current_user_optional
from app.models.user import User
from app.models.like import Like
from app.models.artwork import Artwork
from app.services import artist_descriptions

router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="/app/frontend/www/templates")


@router.get("/me/likes", response_class=HTMLResponse)
async def my_likes_page(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Render the My Likes page showing user's liked artworks and statistics.
    
    Requires authentication. Redirects to login if not authenticated.
    """
    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/login?next=/me/likes", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get liked artworks
    artworks_query = (
        select(Artwork)
        .join(Like, Like.artwork_id == Artwork.id)
        .where(Like.user_id == current_user.id)
        .order_by(Like.created_at.desc())
    )
    artworks_result = await db.execute(artworks_query)
    liked_artworks = artworks_result.scalars().all()
    
    # Add artist descriptions to artworks
    artworks_with_descriptions = []
    for artwork in liked_artworks:
        description = artist_descriptions.get_description_snippet(artwork.artist)
        artworks_with_descriptions.append({
            'artwork': artwork,
            'description': description
        })
    
    # Get style statistics
    stats_query = (
        select(
            Artwork.style,
            func.count(Like.id).label('count')
        )
        .join(Like, Like.artwork_id == Artwork.id)
        .where(Like.user_id == current_user.id)
        .group_by(Artwork.style)
        .order_by(func.count(Like.id).desc())
    )
    stats_result = await db.execute(stats_query)
    style_counts = stats_result.all()
    
    # Calculate total and percentages
    total_likes = sum(count for _, count in style_counts)
    
    style_stats = []
    if total_likes > 0:
        for style, count in style_counts:
            percentage = round((count / total_likes) * 100, 1)
            style_stats.append({
                'style': style,
                'count': count,
                'percentage': percentage
            })
    
    return templates.TemplateResponse(
        request=request,
        name="me_likes.html",
        context={
            "user": current_user,
            "artworks": artworks_with_descriptions,
            "style_stats": style_stats,
            "total_likes": total_likes
        }
    )
