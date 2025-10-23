"""
Main FastAPI application for Classic Art Gallery.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.init_db import init_db
from app.api.routes import health, artworks, auth, likes, comments, artists
from app.api.deps import get_db
from app.models.artwork import Artwork
from app.web import routes as web_routes
from app.web import likes_routes, admin_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup: Create database tables
    await init_db()
    yield


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: mount the more specific path FIRST to avoid shadowing by /static
app.mount("/static/artworks", StaticFiles(directory="/app/ml/input/wikiart", check_dir=False), name="artworks")
# Static files for web frontend (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="/app/frontend/www/static", check_dir=False), name="static")

# Include API routers
app.include_router(health.router, tags=["health"])
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"],
)
app.include_router(
    artworks.router,
    prefix=settings.API_V1_STR,
    tags=["artworks"],
)
app.include_router(
    likes.router,
    prefix=settings.API_V1_STR,
    tags=["likes"],
)
app.include_router(
    comments.router,
    prefix=settings.API_V1_STR,
    tags=["comments"],
)
app.include_router(
    artists.router,
    tags=["artists"],
)

# Include web routes (HTML pages)
app.include_router(web_routes.router, tags=["web"])
app.include_router(likes_routes.router, tags=["web"])
app.include_router(admin_routes.router, tags=["admin"])

# Keep login and artwork detail pages for now (can be moved to web router later)
templates = Jinja2Templates(directory="/app/frontend/www/templates")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Render the password reset page."""
    return templates.TemplateResponse(request=request, name="reset_password.html")

@app.get("/artworks/{artwork_id}", response_class=HTMLResponse)
async def artwork_detail_page(
    request: Request, 
    artwork_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Render the artwork detail page with artist description."""
    from uuid import UUID
    from app.services import artist_descriptions
    
    # Fetch the artwork from database
    try:
        artwork_uuid = UUID(artwork_id)
        query = select(Artwork).where(Artwork.id == artwork_uuid)
        result = await db.execute(query)
        artwork = result.scalar_one_or_none()
        
        if artwork:
            # Get artist description
            artist_description = artist_descriptions.get_description(artwork.artist)
        else:
            artist_description = None
    except Exception as e:
        artist_description = None
    
    return templates.TemplateResponse(
        request=request, 
        name="artwork_detail.html",
        context={
            "artist_description": artist_description
        }
    )
