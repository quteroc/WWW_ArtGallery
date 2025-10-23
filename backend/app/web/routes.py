"""
Web routes for HTML gallery pages.
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from sqlmodel import col
from app.api.deps import get_db
from app.models.artwork import Artwork
from app.services import artist_descriptions

router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="/app/frontend/www/templates")


@router.get("/", response_class=HTMLResponse)
async def gallery(
    request: Request,
    q: Optional[str] = Query(None, description="Search in title/artist"),
    style: Optional[str] = Query(None, description="Filter by style"),
    page: int = Query(0, ge=0, description="Page number"),
    per_page: int = Query(24, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Render the gallery page with artwork grid.
    
    Supports:
    - q: search query for title/artist (case-insensitive)
    - style: exact style filter
    - page: pagination page number
    - per_page: items per page (default 24)
    """
    # Build query for artworks
    query = select(Artwork).where(Artwork.is_active == True)
    
    # Apply search filter
    if q:
        search_term = f"%{q}%"
        query = query.where(
            (Artwork.title.ilike(search_term)) | (Artwork.artist.ilike(search_term))
        )
    
    # Apply style filter
    if style:
        query = query.where(Artwork.style == style)
    
    # Order by created_at desc
    query = query.order_by(col(Artwork.created_at).desc())
    
    # Apply pagination
    offset = page * per_page
    query = query.offset(offset).limit(per_page)
    
    # Execute query
    result = await db.execute(query)
    artworks = result.scalars().all()
    
    # Add artist descriptions to artworks
    artworks_with_descriptions = []
    for artwork in artworks:
        description = artist_descriptions.get_description_snippet(artwork.artist)
        full_description = artist_descriptions.get_description(artwork.artist)
        artworks_with_descriptions.append({
            'artwork': artwork,
            'description_snippet': description,
            'full_description': full_description
        })
    
    # Get available styles for filter dropdown
    styles_query = select(distinct(Artwork.style)).where(Artwork.is_active == True).order_by(Artwork.style)
    styles_result = await db.execute(styles_query)
    available_styles = styles_result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "artworks": artworks_with_descriptions,
            "available_styles": available_styles,
            "current_style": style,
            "search_query": q or "",
            "page": page,
            "per_page": per_page,
        }
    )
