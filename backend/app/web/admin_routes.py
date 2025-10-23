"""
Admin web routes for management pages.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.api.deps import get_db, get_current_user_optional
from app.models.user import User
from app.models.artwork import Artwork

router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="/app/frontend/www/templates")


def require_admin(current_user: Optional[User]) -> User:
    """
    Helper to check if user is authenticated and has admin role.
    Redirects to home if not.
    """
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    return current_user


def require_manager_or_admin(current_user: Optional[User]) -> User:
    """
    Helper to check if user is authenticated and has manager or admin role.
    Redirects to home if not.
    """
    if not current_user or current_user.role not in ["manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    return current_user


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Render the admin/manager dashboard with statistics.
    
    Requires manager or admin role. Redirects to home if not.
    """
    try:
        current_user = require_manager_or_admin(current_user)
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get counts
    artworks_count_query = select(func.count(Artwork.id))
    artworks_result = await db.execute(artworks_count_query)
    artworks_count = artworks_result.scalar()
    
    users_count_query = select(func.count(User.id))
    users_result = await db.execute(users_count_query)
    users_count = users_result.scalar()
    
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": current_user,
            "artworks_count": artworks_count,
            "users_count": users_count
        }
    )


@router.get("/admin/artworks", response_class=HTMLResponse)
async def admin_artworks(
    request: Request,
    page: int = 0,
    per_page: int = 50,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Render the admin/manager artworks management page.
    
    Supports search by title or artist name via 'q' query parameter.
    Requires manager or admin role. Redirects to home if not.
    """
    try:
        current_user = require_manager_or_admin(current_user)
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Build query for artworks
    query = select(Artwork)
    
    # Apply search filter if provided
    if q:
        search_term = f"%{q}%"
        query = query.where(
            (Artwork.title.ilike(search_term)) | (Artwork.artist.ilike(search_term))
        )
    
    # Apply pagination and ordering
    query = query.order_by(Artwork.created_at.desc()).offset(page * per_page).limit(per_page)
    
    result = await db.execute(query)
    artworks = result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="admin_artworks.html",
        context={
            "user": current_user,
            "artworks": artworks,
            "page": page,
            "per_page": per_page,
            "search_query": q or ""
        }
    )


@router.post("/admin/artworks/{artwork_id}/toggle-active")
async def toggle_artwork_active(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle artwork is_active status.
    
    Requires manager or admin role.
    """
    try:
        current_user = require_manager_or_admin(current_user)
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get artwork
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = await db.execute(query)
    artwork = result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Toggle is_active
    artwork.is_active = not artwork.is_active
    await db.commit()
    
    return RedirectResponse(url="/admin/artworks", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/artworks/{artwork_id}/delete")
async def delete_artwork(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an artwork.
    
    Requires admin role.
    """
    try:
        current_user = require_admin(current_user)
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get artwork
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = await db.execute(query)
    artwork = result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artwork not found"
        )
    
    # Delete artwork
    await db.delete(artwork)
    await db.commit()
    
    return RedirectResponse(url="/admin/artworks", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    page: int = 0,
    per_page: int = 50,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Render the admin users management page.
    
    Requires admin role. Redirects to home if not admin.
    """
    try:
        current_user = require_admin(current_user)
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get users with pagination
    query = (
        select(User)
        .order_by(User.created_at.desc())
        .offset(page * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    users = result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={
            "user": current_user,
            "users": users,
            "page": page,
            "per_page": per_page
        }
    )


@router.post("/admin/users/{user_id}/change-role")
async def change_user_role(
    user_id: UUID,
    role: str = Form(...),
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Change a user's role.
    
    Requires admin role.
    """
    try:
        current_user = require_admin(current_user)
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Validate role
    if role not in ["user", "manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update role
    user.role = role
    await db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)
