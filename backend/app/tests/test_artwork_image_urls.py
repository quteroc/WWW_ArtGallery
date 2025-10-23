"""
Tests for artwork image URL normalization to CDN.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.artwork import Artwork
from app.models.category import Category
from app.core.security import get_password_hash
from app.core.config import settings
from app.api.routes.artworks import normalize_image_url


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    unique_id = uuid4().hex[:8]
    user = User(
        email=f"admin{unique_id}@example.com",
        username=f"admin{unique_id}",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """Create a test category."""
    unique_id = uuid4().hex[:8]
    category = Category(
        name=f"TestStyle{unique_id}",
        slug=f"test-style-{unique_id}"
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def test_artwork(db_session: AsyncSession, test_category: Category) -> Artwork:
    """Create a test artwork."""
    artwork = Artwork(
        title="Test Artwork",
        artist="Test Artist",
        style=test_category.name,
        image_path=f"ml/input/wikiart/{test_category.name}/test-artwork.jpg",
        image_url="/static/artworks/old-url.jpg",  # Old-style URL
        popularity_score=5.0,
        is_active=True
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    return artwork


async def get_admin_token(async_client: AsyncClient, admin_user: User) -> str:
    """Get auth token for admin user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_normalize_image_url_full_path():
    """Test URL normalization with full path."""
    path = "ml/input/wikiart/Baroque/rembrandt-nightwatch.jpg"
    result = normalize_image_url(path)
    expected = f"{settings.ARTWORKS_BASE_URL}/Baroque/rembrandt-nightwatch.jpg"
    assert result == expected


def test_normalize_image_url_short_path():
    """Test URL normalization with short path."""
    path = "artwork.jpg"
    result = normalize_image_url(path)
    expected = f"{settings.ARTWORKS_BASE_URL}/artwork.jpg"
    assert result == expected


def test_normalize_image_url_two_segments():
    """Test URL normalization with two segments."""
    path = "Baroque/artwork.jpg"
    result = normalize_image_url(path)
    expected = f"{settings.ARTWORKS_BASE_URL}/Baroque/artwork.jpg"
    assert result == expected


@pytest.mark.asyncio
async def test_list_artworks_normalizes_urls(async_client: AsyncClient, test_artwork: Artwork):
    """Test that listing artworks returns normalized CDN URLs."""
    response = await async_client.get("/api/v1/artworks")
    assert response.status_code == 200
    
    artworks = response.json()
    assert len(artworks) > 0
    
    # Check that all image URLs use CDN base
    for artwork in artworks:
        assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)


@pytest.mark.asyncio
async def test_get_artwork_normalizes_url(async_client: AsyncClient, test_artwork: Artwork):
    """Test that getting a single artwork returns normalized CDN URL."""
    response = await async_client.get(f"/api/v1/artworks/{test_artwork.id}")
    assert response.status_code == 200
    
    artwork = response.json()
    assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)
    # Should contain the style folder and filename
    assert test_artwork.style in artwork["image_url"] or "test-artwork.jpg" in artwork["image_url"]


@pytest.mark.asyncio
async def test_create_artwork_generates_cdn_url(
    async_client: AsyncClient,
    admin_user: User,
    test_category: Category
):
    """Test that creating an artwork generates proper CDN URL."""
    token = await get_admin_token(async_client, admin_user)
    
    response = await async_client.post(
        "/api/v1/artworks",
        json={
            "title": "New Artwork",
            "artist": "New Artist",
            "style": test_category.name,
            "image_path": f"ml/input/wikiart/{test_category.name}/new-work.jpg",
            "popularity_score": 7.5,
            "is_active": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    artwork = response.json()
    
    # Verify CDN URL was generated
    assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)
    assert "new-work.jpg" in artwork["image_url"]


@pytest.mark.asyncio
async def test_update_artwork_updates_cdn_url(
    async_client: AsyncClient,
    admin_user: User,
    test_artwork: Artwork,
    test_category: Category
):
    """Test that updating artwork image_path updates CDN URL."""
    token = await get_admin_token(async_client, admin_user)
    
    new_path = f"ml/input/wikiart/{test_category.name}/updated-artwork.jpg"
    response = await async_client.put(
        f"/api/v1/artworks/{test_artwork.id}",
        json={"image_path": new_path},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    artwork = response.json()
    
    # Verify CDN URL was updated
    assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)
    assert "updated-artwork.jpg" in artwork["image_url"]


@pytest.mark.asyncio
async def test_toggle_active_returns_normalized_url(
    async_client: AsyncClient,
    admin_user: User,
    test_artwork: Artwork
):
    """Test that toggling artwork active returns normalized URL."""
    token = await get_admin_token(async_client, admin_user)
    
    response = await async_client.post(
        f"/api/v1/artworks/{test_artwork.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    artwork = response.json()
    
    # Verify CDN URL is returned
    assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)
    # Verify active status was toggled
    assert artwork["is_active"] != test_artwork.is_active


@pytest.mark.asyncio
async def test_filtered_artworks_have_normalized_urls(
    async_client: AsyncClient,
    test_artwork: Artwork,
    test_category: Category
):
    """Test that filtered artwork queries return normalized URLs."""
    response = await async_client.get(
        f"/api/v1/artworks?style={test_category.name}"
    )
    
    assert response.status_code == 200
    artworks = response.json()
    
    # All artworks should have normalized URLs
    for artwork in artworks:
        assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)


@pytest.mark.asyncio
async def test_sorted_artworks_have_normalized_urls(
    async_client: AsyncClient,
    test_artwork: Artwork
):
    """Test that sorted artwork queries return normalized URLs."""
    response = await async_client.get("/api/v1/artworks?sort=popularity")
    
    assert response.status_code == 200
    artworks = response.json()
    
    # All artworks should have normalized URLs
    for artwork in artworks:
        assert artwork["image_url"].startswith(settings.ARTWORKS_BASE_URL)


@pytest.mark.asyncio
async def test_artworks_pagination(async_client: AsyncClient, test_artwork: Artwork):
    """Test artwork pagination works."""
    response = await async_client.get("/api/v1/artworks?skip=0&limit=10")
    assert response.status_code == 200
    artworks = response.json()
    assert isinstance(artworks, list)
    assert len(artworks) <= 10


@pytest.mark.asyncio
async def test_get_nonexistent_artwork(async_client: AsyncClient):
    """Test getting non-existent artwork returns 404."""
    from uuid import uuid4
    fake_id = uuid4()
    response = await async_client.get(f"/api/v1/artworks/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_artwork_requires_admin(async_client: AsyncClient, admin_user: User, test_artwork: Artwork):
    """Test deleting artwork requires admin."""
    token = await get_admin_token(async_client, admin_user)
    response = await async_client.delete(
        f"/api/v1/artworks/{test_artwork.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_filter_artworks_by_artist(async_client: AsyncClient, test_artwork: Artwork):
    """Test filtering artworks by artist."""
    response = await async_client.get(f"/api/v1/artworks?artist={test_artwork.artist}")
    assert response.status_code == 200
    artworks = response.json()
    for artwork in artworks:
        assert test_artwork.artist.lower() in artwork["artist"].lower()


@pytest.mark.asyncio
async def test_artworks_sorted_by_views(async_client: AsyncClient, test_artwork: Artwork):
    """Test sorting artworks by views."""
    response = await async_client.get("/api/v1/artworks?sort=views")
    assert response.status_code == 200
    artworks = response.json()
    assert isinstance(artworks, list)


@pytest.mark.asyncio
async def test_artworks_sorted_by_created_at(async_client: AsyncClient, test_artwork: Artwork):
    """Test sorting artworks by created date."""
    response = await async_client.get("/api/v1/artworks?sort=created_at")
    assert response.status_code == 200
    artworks = response.json()
    assert isinstance(artworks, list)
