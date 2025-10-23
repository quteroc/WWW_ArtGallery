"""
Tests for artwork API endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.artwork import Artwork


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test root endpoint returns gallery page."""
    response = await async_client.get("/")
    assert response.status_code == 200
    # Root endpoint now returns HTML gallery page
    assert b"Art Gallery" in response.content


@pytest.mark.asyncio
async def test_get_artworks_empty(async_client: AsyncClient):
    """Test getting artworks when database is empty."""
    response = await async_client.get("/api/v1/artworks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_create_and_get_artwork(async_client: AsyncClient, db_session: AsyncSession):
    """Test creating and retrieving an artwork."""
    # First, create a category
    category = Category(name="Baroque", slug="baroque")
    db_session.add(category)
    await db_session.commit()
    
    # Create an artwork
    artwork_data = {
        "title": "The Night Watch",
        "artist": "Rembrandt",
        "year": 1642,
        "style": "Baroque",
        "image_path": "ml/input/wikiart/Baroque/rembrandt-night-watch.jpg",
        "image_url": "/static/artworks/Baroque/rembrandt-night-watch.jpg",
        "popularity_score": 0.95,
        "views": 0,
        "is_active": True
    }
    
    response = await async_client.post("/api/v1/artworks", json=artwork_data)
    assert response.status_code == 200
    created = response.json()
    assert created["title"] == "The Night Watch"
    assert created["artist"] == "Rembrandt"
    assert "id" in created
    
    # Get all artworks
    response = await async_client.get("/api/v1/artworks")
    assert response.status_code == 200
    artworks = response.json()
    assert len(artworks) == 1
    assert artworks[0]["title"] == "The Night Watch"


@pytest.mark.asyncio
async def test_get_artworks_sorted_by_popularity(async_client: AsyncClient, db_session: AsyncSession):
    """Test sorting artworks by popularity score."""
    # Create category with unique name
    category = Category(name="Impressionism_Sort", slug="impressionism-sort")
    db_session.add(category)
    await db_session.commit()
    
    # Create artworks with different popularity scores
    artworks = [
        Artwork(
            title="Water Lilies",
            artist="Claude Monet",
            style="Impressionism_Sort",
            image_path="ml/input/wikiart/Impressionism/monet-water-lilies.jpg",
            image_url="/static/artworks/Impressionism/monet-water-lilies.jpg",
            popularity_score=0.9,
        ),
        Artwork(
            title="Impression Sunrise",
            artist="Claude Monet",
            style="Impressionism_Sort",
            image_path="ml/input/wikiart/Impressionism/monet-sunrise.jpg",
            image_url="/static/artworks/Impressionism/monet-sunrise.jpg",
            popularity_score=0.7,
        ),
        Artwork(
            title="Woman with a Parasol",
            artist="Claude Monet",
            style="Impressionism_Sort",
            image_path="ml/input/wikiart/Impressionism/monet-parasol.jpg",
            image_url="/static/artworks/Impressionism/monet-parasol.jpg",
            popularity_score=0.5,
        ),
    ]
    
    for artwork in artworks:
        db_session.add(artwork)
    await db_session.commit()
    
    # Get artworks sorted by popularity for this category
    response = await async_client.get("/api/v1/artworks?sort=popularity&style=Impressionism_Sort")
    assert response.status_code == 200
    result = response.json()
    scores = [a["popularity_score"] for a in result]
    assert scores == sorted(scores, reverse=True)
    assert len(scores) >= 3
    assert scores[0] == 0.9


@pytest.mark.asyncio
async def test_filter_artworks_by_style(async_client: AsyncClient, db_session: AsyncSession):
    """Test filtering artworks by style."""
    # Create categories with unique names
    baroque = Category(name="Baroque_Filter", slug="baroque-filter")
    impressionism = Category(name="Impressionism_Filter", slug="impressionism-filter")
    db_session.add(baroque)
    db_session.add(impressionism)
    await db_session.commit()
    
    # Create artworks in different styles
    artwork1 = Artwork(
        title="The Night Watch",
        artist="Rembrandt",
        style="Baroque_Filter",
        image_path="ml/input/wikiart/Baroque/rembrandt-night-watch.jpg",
        image_url="/static/artworks/Baroque/rembrandt-night-watch.jpg",
        popularity_score=0.95,
    )
    artwork2 = Artwork(
        title="Water Lilies",
        artist="Claude Monet",
        style="Impressionism_Filter",
        image_path="ml/input/wikiart/Impressionism/monet-water-lilies.jpg",
        image_url="/static/artworks/Impressionism/monet-water-lilies.jpg",
        popularity_score=0.9,
    )
    
    db_session.add(artwork1)
    db_session.add(artwork2)
    await db_session.commit()
    
    # Filter by Baroque
    response = await async_client.get("/api/v1/artworks?style=Baroque_Filter")
    assert response.status_code == 200
    artworks = response.json()
    assert len(artworks) == 1
    assert artworks[0]["style"] == "Baroque_Filter"
    assert artworks[0]["title"] == "The Night Watch"


@pytest.mark.asyncio
async def test_get_categories(async_client: AsyncClient, db_session: AsyncSession):
    """Test getting all categories."""
    # Create some categories with unique names
    categories = [
        Category(name="Baroque_GetCat", slug="baroque-getcat"),
        Category(name="Impressionism_GetCat", slug="impressionism-getcat"),
        Category(name="Renaissance_GetCat", slug="renaissance-getcat"),
    ]
    
    for category in categories:
        db_session.add(category)
    await db_session.commit()
    
    # Get categories
    response = await async_client.get("/api/v1/categories")
    assert response.status_code == 200
    result = response.json()
    # Check we have at least our 3 categories (there may be more from other tests)
    assert len(result) >= 3
    assert all("name" in c for c in result)
    assert all("slug" in c for c in result)


@pytest.mark.asyncio
async def test_get_single_artwork(async_client: AsyncClient, db_session: AsyncSession):
    """Test getting a single artwork by ID."""
    # Create category and artwork with unique name
    category = Category(name="Baroque_Single", slug="baroque-single")
    db_session.add(category)
    await db_session.commit()
    
    artwork = Artwork(
        title="The Night Watch",
        artist="Rembrandt",
        style="Baroque_Single",
        image_path="ml/input/wikiart/Baroque/rembrandt-night-watch.jpg",
        image_url="/static/artworks/Baroque/rembrandt-night-watch.jpg",
        popularity_score=0.95,
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    
    # Get the artwork by ID
    response = await async_client.get(f"/api/v1/artworks/{artwork.id}")
    assert response.status_code == 200
    result = response.json()
    assert result["title"] == "The Night Watch"
    assert result["artist"] == "Rembrandt"


@pytest.mark.asyncio
async def test_get_nonexistent_artwork(async_client: AsyncClient):
    """Test getting an artwork that doesn't exist."""
    fake_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await async_client.get(f"/api/v1/artworks/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination(async_client: AsyncClient, db_session: AsyncSession):
    """Test artwork pagination."""
    # Create category
    category = Category(name="Test", slug="test")
    db_session.add(category)
    await db_session.commit()
    
    # Create multiple artworks
    for i in range(15):
        artwork = Artwork(
            title=f"Artwork {i}",
            artist="Test Artist",
            style="Test",
            image_path=f"test{i}.jpg",
            image_url=f"/static/test{i}.jpg",
            popularity_score=float(i),
        )
        db_session.add(artwork)
    await db_session.commit()
    
    # Get first page (default limit is 20, so all should fit)
    response = await async_client.get("/api/v1/artworks?limit=5")
    assert response.status_code == 200
    artworks = response.json()
    assert len(artworks) == 5
    
    # Get second page
    response = await async_client.get("/api/v1/artworks?skip=5&limit=5")
    assert response.status_code == 200
    artworks = response.json()
    assert len(artworks) == 5
