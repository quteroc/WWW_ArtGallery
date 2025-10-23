"""
Tests for web gallery routes.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.artwork import Artwork


@pytest.mark.asyncio
async def test_gallery_page_loads(async_client: AsyncClient):
    """Test that the gallery page loads successfully."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert b"Art Gallery" in response.content


@pytest.mark.asyncio
async def test_gallery_displays_artwork(async_client: AsyncClient, db_session: AsyncSession):
    """Test that gallery displays artwork when data exists."""
    # Create category
    category = Category(name="TestGallery", slug="test-gallery")
    db_session.add(category)
    await db_session.commit()
    
    # Create artwork
    artwork = Artwork(
        title="Test Gallery Artwork",
        artist="Test Artist",
        style="TestGallery",
        image_path="ml/input/wikiart/TestGallery/test.jpg",
        image_url="/static/artworks/TestGallery/test.jpg",
        popularity_score=0.8,
        is_active=True,
    )
    db_session.add(artwork)
    await db_session.commit()
    
    # Get gallery page
    response = await async_client.get("/")
    assert response.status_code == 200
    content = response.content.decode()
    
    # Check that artwork is displayed
    assert "Test Gallery Artwork" in content
    assert "Test Artist" in content
    assert "/static/artworks/TestGallery/test.jpg" in content


@pytest.mark.asyncio
async def test_gallery_search_filter(async_client: AsyncClient, db_session: AsyncSession):
    """Test that gallery search filter works."""
    # Create category
    category = Category(name="SearchTest", slug="search-test")
    db_session.add(category)
    await db_session.commit()
    
    # Create artworks
    artwork1 = Artwork(
        title="Monet Water Lilies",
        artist="Claude Monet",
        style="SearchTest",
        image_path="ml/input/wikiart/SearchTest/monet.jpg",
        image_url="/static/artworks/SearchTest/monet.jpg",
        popularity_score=0.9,
        is_active=True,
    )
    artwork2 = Artwork(
        title="Van Gogh Starry Night",
        artist="Vincent van Gogh",
        style="SearchTest",
        image_path="ml/input/wikiart/SearchTest/vangogh.jpg",
        image_url="/static/artworks/SearchTest/vangogh.jpg",
        popularity_score=0.95,
        is_active=True,
    )
    db_session.add(artwork1)
    db_session.add(artwork2)
    await db_session.commit()
    
    # Search for "monet"
    response = await async_client.get("/?q=monet")
    assert response.status_code == 200
    content = response.content.decode()
    
    # Should find Monet but not Van Gogh
    assert "Monet Water Lilies" in content
    assert "Van Gogh Starry Night" not in content


@pytest.mark.asyncio
async def test_gallery_style_filter(async_client: AsyncClient, db_session: AsyncSession):
    """Test that gallery style filter works."""
    # Create categories
    baroque = Category(name="Baroque_Style", slug="baroque-style")
    impressionism = Category(name="Impressionism_Style", slug="impressionism-style")
    db_session.add(baroque)
    db_session.add(impressionism)
    await db_session.commit()
    
    # Create artworks
    artwork1 = Artwork(
        title="Baroque Artwork",
        artist="Baroque Artist",
        style="Baroque_Style",
        image_path="ml/input/wikiart/Baroque/art1.jpg",
        image_url="/static/artworks/Baroque/art1.jpg",
        popularity_score=0.8,
        is_active=True,
    )
    artwork2 = Artwork(
        title="Impressionism Artwork",
        artist="Impressionism Artist",
        style="Impressionism_Style",
        image_path="ml/input/wikiart/Impressionism/art2.jpg",
        image_url="/static/artworks/Impressionism/art2.jpg",
        popularity_score=0.85,
        is_active=True,
    )
    db_session.add(artwork1)
    db_session.add(artwork2)
    await db_session.commit()
    
    # Filter by Baroque style
    response = await async_client.get("/?style=Baroque_Style")
    assert response.status_code == 200
    content = response.content.decode()
    
    # Should find Baroque but not Impressionism
    assert "Baroque Artwork" in content
    assert "Impressionism Artwork" not in content


@pytest.mark.asyncio
async def test_gallery_pagination(async_client: AsyncClient, db_session: AsyncSession):
    """Test that gallery pagination works."""
    # Create category
    category = Category(name="PaginationTest", slug="pagination-test")
    db_session.add(category)
    await db_session.commit()
    
    # Create multiple artworks
    for i in range(30):
        artwork = Artwork(
            title=f"Artwork {i}",
            artist=f"Artist {i}",
            style="PaginationTest",
            image_path=f"ml/input/wikiart/PaginationTest/art{i}.jpg",
            image_url=f"/static/artworks/PaginationTest/art{i}.jpg",
            popularity_score=float(i) / 100.0,
            is_active=True,
        )
        db_session.add(artwork)
    await db_session.commit()
    
    # Get first page (default 24 items)
    response = await async_client.get("/?per_page=10")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Page 1" in content
    
    # Get second page
    response = await async_client.get("/?page=1&per_page=10")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Page 2" in content


@pytest.mark.asyncio
async def test_gallery_only_shows_active_artworks(async_client: AsyncClient, db_session: AsyncSession):
    """Test that gallery only shows active artworks."""
    # Create category
    category = Category(name="ActiveTest", slug="active-test")
    db_session.add(category)
    await db_session.commit()
    
    # Create active artwork
    active_artwork = Artwork(
        title="Active Artwork",
        artist="Active Artist",
        style="ActiveTest",
        image_path="ml/input/wikiart/ActiveTest/active.jpg",
        image_url="/static/artworks/ActiveTest/active.jpg",
        popularity_score=0.8,
        is_active=True,
    )
    
    # Create inactive artwork
    inactive_artwork = Artwork(
        title="Inactive Artwork",
        artist="Inactive Artist",
        style="ActiveTest",
        image_path="ml/input/wikiart/ActiveTest/inactive.jpg",
        image_url="/static/artworks/ActiveTest/inactive.jpg",
        popularity_score=0.9,
        is_active=False,
    )
    
    db_session.add(active_artwork)
    db_session.add(inactive_artwork)
    await db_session.commit()
    
    # Get gallery page
    response = await async_client.get("/")
    assert response.status_code == 200
    content = response.content.decode()
    
    # Should show active but not inactive
    assert "Active Artwork" in content
    assert "Inactive Artwork" not in content
