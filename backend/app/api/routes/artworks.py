"""
Artworks API endpoints.
"""
import os
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlmodel import col
from app.api.deps import get_db, require_roles
from app.models.artwork import Artwork
from app.models.category import Category
from app.models.user import User
from app.schemas.artwork import ArtworkCreate, ArtworkUpdate, ArtworkImport
from app.services import artist_descriptions  # NEW
from app.core.config import settings

router = APIRouter()


def normalize_image_url(image_path: str) -> str:
    """
    Convert image_path to absolute URL using DigitalOcean Spaces CDN.
    
    Prefers last two segments (Style/filename.jpg) from the path.
    Example: "ml/input/wikiart/Baroque/artist-title.jpg" -> 
             "https://artappspace.nyc3.digitaloceanspaces.com/Baroque/artist-title.jpg"
    """
    parts = image_path.split("/")
    if len(parts) >= 2:
        # Take last two segments: Style/filename.jpg
        style_and_file = "/".join(parts[-2:])
    else:
        # Fallback to just the filename
        style_and_file = parts[-1] if parts else image_path
    
    # Remove any leading slashes from the style_and_file
    style_and_file = style_and_file.lstrip("/")
    
    # Construct absolute URL
    base_url = settings.ARTWORKS_BASE_URL.rstrip("/")
    return f"{base_url}/{style_and_file}"


@router.get("/artworks", response_model=List[Artwork])
async def list_artworks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("popularity", pattern="^(popularity|views|created_at)$"),
    style: Optional[str] = None,
    artist: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List artworks with pagination and filtering.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 20, max: 100)
    - **sort**: Sort field - popularity, views, or created_at (default: popularity)
    - **style**: Filter by art style/category
    - **artist**: Filter by artist name
    """
    query = select(Artwork).where(Artwork.is_active == True)
    
    # Apply filters
    if style:
        query = query.where(Artwork.style == style)
    if artist:
        query = query.where(Artwork.artist.ilike(f"%{artist}%"))
    
    # Apply sorting
    if sort == "popularity":
        query = query.order_by(col(Artwork.popularity_score).desc())
    elif sort == "views":
        query = query.order_by(col(Artwork.views).desc())
    elif sort == "created_at":
        query = query.order_by(col(Artwork.created_at).desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    artworks = result.scalars().all()
    
    # Normalize image URLs to use Spaces CDN
    for artwork in artworks:
        artwork.image_url = normalize_image_url(artwork.image_path)
    
    return artworks


@router.get("/artworks/{artwork_id}", response_model=Artwork)
async def get_artwork(artwork_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single artwork by ID."""
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = await db.execute(query)
    artwork = result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    # Normalize image URL to use Spaces CDN
    artwork.image_url = normalize_image_url(artwork.image_path)
    
    return artwork


# NEW: Full artist description endpoint for detail page
@router.get("/artworks/{artwork_id}/artist-description")
async def get_artist_description(artwork_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Return the best available full artist description for the artwork's artist.
    Falls back to an empty string if no description is available.
    """
    result = await db.execute(select(Artwork).where(Artwork.id == artwork_id))
    artwork = result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    desc = artist_descriptions.get_description(artwork.artist) or ""
    return {"artist": artwork.artist, "description": desc}


@router.get("/categories", response_model=List[Category])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all art styles/categories."""
    query = select(Category)
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return categories


# Admin endpoints (protected by role-based authentication)
@router.post("/artworks", response_model=Artwork, dependencies=[Depends(require_roles("admin"))])
async def create_artwork(
    artwork_data: ArtworkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """Create a new artwork (admin only).
    
    Requires admin role and valid JWT token.
    """
    # Generate image_url from image_path using Spaces CDN
    image_url = normalize_image_url(artwork_data.image_path)
    
    artwork = Artwork(
        title=artwork_data.title,
        artist=artwork_data.artist,
        year=artwork_data.year,
        style=artwork_data.style,
        image_path=artwork_data.image_path,
        image_url=image_url,
        popularity_score=artwork_data.popularity_score,
        is_active=artwork_data.is_active
    )
    
    db.add(artwork)
    await db.commit()
    await db.refresh(artwork)
    return artwork


@router.put("/artworks/{artwork_id}", response_model=Artwork, dependencies=[Depends(require_roles("admin"))])
async def update_artwork(
    artwork_id: UUID,
    artwork_update: ArtworkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """Update an artwork (admin only).
    
    Requires admin role and valid JWT token.
    """
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = await db.execute(query)
    artwork = result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    # Update fields
    update_data = artwork_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(artwork, key, value)
    
    # Update image_url if image_path changed
    if "image_path" in update_data:
        artwork.image_url = normalize_image_url(artwork.image_path)
    
    from datetime import datetime
    artwork.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(artwork)
    
    # Normalize image URL before returning
    artwork.image_url = normalize_image_url(artwork.image_path)
    
    return artwork


@router.delete("/artworks/{artwork_id}", dependencies=[Depends(require_roles("admin"))])
async def delete_artwork(
    artwork_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """Soft delete an artwork by setting is_active to False (admin only).
    
    Requires admin role and valid JWT token.
    """
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = await db.execute(query)
    artwork = result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    artwork.is_active = False
    await db.commit()
    
    return {"message": "Artwork deleted successfully"}


@router.post("/artworks/import-from-path", response_model=Artwork, dependencies=[Depends(require_roles("admin"))])
async def import_artwork_from_path(
    import_data: ArtworkImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """Import artwork from file path (admin only).
    
    - **image_path**: Path like "ml/input/wikiart/Baroque/artist-title.jpg"
    - **title**: Optional. If not provided, parsed from filename
    - **artist**: Optional. If not provided, parsed from filename
    - **style**: Optional. If not provided, inferred from folder name
    
    Note: File existence checks are relaxed to support Spaces CDN hosting.
    Filename format expected: "artist-title.jpg" or similar.
    """
    # Relaxed file existence check - we're using Spaces CDN now
    # Only warn if file doesn't exist locally, but don't fail
    file_exists = False
    check_paths = [
        import_data.image_path,  # Relative path
        os.path.join("/app", import_data.image_path),  # Docker container path
        os.path.join(os.path.dirname(__file__), "../../../..", import_data.image_path)  # Local dev
    ]
    
    for check_path in check_paths:
        if os.path.exists(check_path):
            file_exists = True
            break
    
    # Note: We don't raise an error if file doesn't exist locally
    # since images are hosted on Spaces CDN
    
    # Parse style from folder if not provided
    style = import_data.style
    if not style:
        # Extract style from path: "ml/input/wikiart/Baroque/filename.jpg" -> "Baroque"
        parts = import_data.image_path.split("/")
        if len(parts) >= 2:
            style = parts[-2]  # Second to last part is the style folder
        else:
            raise HTTPException(
                status_code=400,
                detail="Could not infer style from path. Please provide style explicitly."
            )
    
    # Parse title and artist from filename if not provided
    filename = os.path.basename(import_data.image_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    title = import_data.title
    artist = import_data.artist
    
    if not title or not artist:
        # Try to parse from filename (common format: "artist-title.jpg")
        parts = name_without_ext.split("-", 1)
        if len(parts) >= 2:
            if not artist:
                artist = parts[0].strip().replace("_", " ").title()
            if not title:
                title = parts[1].strip().replace("_", " ").title()
        else:
            # Fallback: use filename as title
            if not title:
                title = name_without_ext.replace("_", " ").title()
            if not artist:
                artist = "Unknown"
    
    # Generate image_url using Spaces CDN
    image_url = normalize_image_url(import_data.image_path)
    
    # Create artwork
    artwork = Artwork(
        title=title,
        artist=artist,
        style=style,
        image_path=import_data.image_path,
        image_url=image_url,
        popularity_score=0.0,
        is_active=True
    )
    
    db.add(artwork)
    await db.commit()
    await db.refresh(artwork)
    
    return artwork


@router.post("/artworks/{artwork_id}/toggle-active", response_model=Artwork, dependencies=[Depends(require_roles("admin", "manager"))])
async def toggle_artwork_active(
    artwork_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager"))
):
    """Toggle the is_active status of an artwork (admin or manager).
    
    Flips is_active between True and False.
    """
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = await db.execute(query)
    artwork = result.scalar_one_or_none()
    
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    # Toggle is_active
    artwork.is_active = not artwork.is_active
    
    from datetime import datetime
    artwork.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(artwork)
    
    # Normalize image URL before returning
    artwork.image_url = normalize_image_url(artwork.image_path)
    
    return artwork


@router.get("/artworks/available/scan", dependencies=[Depends(require_roles("admin"))])
async def scan_available_artworks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Scan the WikiArt directory and return available artworks grouped by style.
    Only returns artworks that are NOT already in the database.
    
    Returns:
        {
            "Baroque": [
                {"path": "Baroque/rembrandt-night_watch.jpg", "title": "Night Watch", "artist": "Rembrandt"},
                ...
            ],
            "Impressionism": [...],
            ...
        }
    """
    import re
    from pathlib import Path
    
    wikiart_dir = Path(settings.STATIC_FILES_DIR)
    
    if not wikiart_dir.exists():
        return {}
    
    # Get all existing artwork paths from database
    query = select(Artwork.image_path)
    result = await db.execute(query)
    existing_paths = set(result.scalars().all())
    
    available_artworks = {}
    
    # Scan directory
    for style_dir in wikiart_dir.iterdir():
        if not style_dir.is_dir():
            continue
            
        style_name = style_dir.name
        available_artworks[style_name] = []
        
        # Scan images in style directory (limit to 100 per style for performance)
        image_count = 0
        for img_file in style_dir.glob("*.jpg"):
            if image_count >= 100:
                break
                
            relative_path = f"{style_name}/{img_file.name}"
            
            # Skip if already in database
            if any(relative_path in path for path in existing_paths):
                continue
            
            # Parse filename: "artist-name_title-name.jpg"
            filename = img_file.stem  # Remove .jpg
            
            # Split by underscore or hyphen to extract artist and title
            if "_" in filename:
                parts = filename.split("_", 1)
                artist_part = parts[0]
                title_part = parts[1] if len(parts) > 1 else parts[0]
            else:
                # Fallback: use first part as artist, rest as title
                parts = filename.split("-", 1)
                artist_part = parts[0]
                title_part = parts[1] if len(parts) > 1 else parts[0]
            
            # Format: replace hyphens/underscores with spaces, title case
            artist = artist_part.replace("-", " ").replace("_", " ").title()
            title = title_part.replace("-", " ").replace("_", " ").title()
            
            available_artworks[style_name].append({
                "path": relative_path,
                "title": title,
                "artist": artist
            })
            image_count += 1
        
        # Remove empty styles
        if not available_artworks[style_name]:
            del available_artworks[style_name]
    
    return available_artworks


@router.post("/artworks/batch-import", dependencies=[Depends(require_roles("admin"))])
async def batch_import_artworks(
    artwork_paths: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Import multiple artworks at once from a list of paths.
    
    Args:
        artwork_paths: List of image paths relative to WikiArt directory
        
    Returns:
        {"imported": 5, "failed": 0, "details": [...]}
    """
    import re
    
    imported = 0
    failed = 0
    details = []
    
    for image_path in artwork_paths:
        try:
            # Parse style, artist, and title from path
            # Format: "Style/artist-name_title-name.jpg"
            parts = image_path.split("/")
            
            if len(parts) < 2:
                details.append({"path": image_path, "status": "failed", "error": "Invalid path format"})
                failed += 1
                continue
            
            style = parts[0]
            filename = parts[1].replace(".jpg", "").replace(".png", "")
            
            # Parse filename
            if "_" in filename:
                file_parts = filename.split("_", 1)
                artist_part = file_parts[0]
                title_part = file_parts[1] if len(file_parts) > 1 else file_parts[0]
            else:
                file_parts = filename.split("-", 1)
                artist_part = file_parts[0]
                title_part = file_parts[1] if len(file_parts) > 1 else file_parts[0]
            
            artist = artist_part.replace("-", " ").replace("_", " ").title()
            title = title_part.replace("-", " ").replace("_", " ").title()
            
            # Generate CDN URL
            image_url = normalize_image_url(image_path)
            
            # Create artwork
            artwork = Artwork(
                title=title,
                artist=artist,
                style=style,
                image_path=image_path,
                image_url=image_url,
                popularity_score=0.0,
                is_active=True
            )
            
            db.add(artwork)
            details.append({
                "path": image_path,
                "status": "success",
                "title": title,
                "artist": artist
            })
            imported += 1
            
        except Exception as e:
            details.append({
                "path": image_path,
                "status": "failed",
                "error": str(e)
            })
            failed += 1
    
    await db.commit()
    
    return {
        "imported": imported,
        "failed": failed,
        "details": details
    }

