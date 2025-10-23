"""
Tests for likes API endpoints.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.models.user import User
from app.models.artwork import Artwork
from app.models.category import Category
from app.models.like import Like
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    # Use unique username for each test
    user = User(
        email=f"testuser{uuid4().hex[:8]}@example.com",
        username=f"testuser{uuid4().hex[:8]}",
        hashed_password=get_password_hash("testpass123"),
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_category(db_session: AsyncSession) -> Category:
    """Create a test category."""
    # Use unique slug for each test
    slug = f"test-style-{uuid4().hex[:8]}"
    category = Category(name=f"Test Style {uuid4().hex[:8]}", slug=slug)
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture(scope="function")
async def test_artwork(db_session: AsyncSession, test_category: Category) -> Artwork:
    """Create a test artwork."""
    artwork = Artwork(
        title="Test Artwork",
        artist="Test Artist",
        style=test_category.name,
        image_path="test/path.jpg",
        image_url="/static/artworks/test/path.jpg",
        popularity_score=0.8,
        is_active=True
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    return artwork


@pytest.fixture(scope="function")
async def auth_headers(async_client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.username, "password": "testpass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_like_artwork(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork
):
    """Test liking an artwork."""
    response = await async_client.post(
        f"/api/v1/likes/{test_artwork.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["liked"] is True
    assert "message" in data


@pytest.mark.asyncio
async def test_like_artwork_already_liked(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork
):
    """Test liking an already liked artwork."""
    # Like first time
    response1 = await async_client.post(
        f"/api/v1/likes/{test_artwork.id}",
        headers=auth_headers
    )
    assert response1.status_code == 200
    
    # Like second time - should still return 200 with message
    response2 = await async_client.post(
        f"/api/v1/likes/{test_artwork.id}",
        headers=auth_headers
    )
    
    assert response2.status_code == 200
    data = response2.json()
    assert data["liked"] is True


@pytest.mark.asyncio
async def test_like_nonexistent_artwork(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test liking a nonexistent artwork."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.post(
        f"/api/v1/likes/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unlike_artwork(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork
):
    """Test unliking an artwork."""
    # Like first
    await async_client.post(
        f"/api/v1/likes/{test_artwork.id}",
        headers=auth_headers
    )
    
    # Unlike
    response = await async_client.delete(
        f"/api/v1/likes/{test_artwork.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["liked"] is False


@pytest.mark.asyncio
async def test_unlike_not_liked_artwork(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork
):
    """Test unliking an artwork that was not liked."""
    response = await async_client.delete(
        f"/api/v1/likes/{test_artwork.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_likes_empty(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test getting likes when user has no likes."""
    response = await async_client.get(
        "/api/v1/likes/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_my_likes(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork,
    db_session: AsyncSession,
    test_category: Category
):
    """Test getting user's liked artworks."""
    # Create another artwork
    artwork2 = Artwork(
        title="Test Artwork 2",
        artist="Test Artist 2",
        style=test_category.name,
        image_path="test/path2.jpg",
        image_url="/static/artworks/test/path2.jpg",
        popularity_score=0.7,
        is_active=True
    )
    db_session.add(artwork2)
    await db_session.commit()
    await db_session.refresh(artwork2)
    
    # Like both artworks
    await async_client.post(f"/api/v1/likes/{test_artwork.id}", headers=auth_headers)
    await async_client.post(f"/api/v1/likes/{artwork2.id}", headers=auth_headers)
    
    # Get likes
    response = await async_client.get("/api/v1/likes/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("id" in item for item in data)
    assert all("title" in item for item in data)
    assert all("artist" in item for item in data)
    assert all("style" in item for item in data)
    assert all("image_url" in item for item in data)


@pytest.mark.asyncio
async def test_get_my_likes_stats_empty(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test getting stats when user has no likes."""
    response = await async_client.get(
        "/api/v1/likes/me/stats",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_my_likes_stats(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork,
    test_category: Category,
    db_session: AsyncSession
):
    """Test getting statistics about liked artworks."""
    # Create artworks in different styles
    category2_slug = f"style-2-{uuid4().hex[:8]}"
    category2 = Category(name=f"Style 2 {uuid4().hex[:8]}", slug=category2_slug)
    db_session.add(category2)
    await db_session.commit()
    await db_session.refresh(category2)
    
    artwork2 = Artwork(
        title="Artwork 2",
        artist="Artist 2",
        style=category2.name,
        image_path="test/path2.jpg",
        image_url="/static/artworks/test/path2.jpg",
        is_active=True
    )
    artwork3 = Artwork(
        title="Artwork 3",
        artist="Artist 3",
        style=category2.name,
        image_path="test/path3.jpg",
        image_url="/static/artworks/test/path3.jpg",
        is_active=True
    )
    db_session.add_all([artwork2, artwork3])
    await db_session.commit()
    await db_session.refresh(artwork2)
    await db_session.refresh(artwork3)
    
    # Like artworks: 1 from style 1, 2 from style 2
    await async_client.post(f"/api/v1/likes/{test_artwork.id}", headers=auth_headers)
    await async_client.post(f"/api/v1/likes/{artwork2.id}", headers=auth_headers)
    await async_client.post(f"/api/v1/likes/{artwork3.id}", headers=auth_headers)
    
    # Get stats
    response = await async_client.get("/api/v1/likes/me/stats", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check stats structure
    for stat in data:
        assert "style" in stat
        assert "count" in stat
        assert "percentage" in stat
    
    # Check percentages sum to 100
    total_percentage = sum(stat["percentage"] for stat in data)
    assert abs(total_percentage - 100.0) < 0.1  # Allow small rounding error
    
    # Check counts
    counts = {stat["style"]: stat["count"] for stat in data}
    assert counts[category2.name] == 2
    assert counts[test_category.name] == 1


@pytest.mark.asyncio
async def test_check_if_liked(
    async_client: AsyncClient,
    auth_headers: dict,
    test_artwork: Artwork
):
    """Test checking if artwork is liked."""
    # Check before liking
    response = await async_client.get(
        f"/api/v1/likes/check/{test_artwork.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["liked"] is False
    
    # Like the artwork
    await async_client.post(f"/api/v1/likes/{test_artwork.id}", headers=auth_headers)
    
    # Check after liking
    response = await async_client.get(
        f"/api/v1/likes/check/{test_artwork.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["liked"] is True


@pytest.mark.asyncio
async def test_likes_require_authentication(async_client: AsyncClient):
    """Test that likes endpoints require authentication."""
    # Create a fake artwork ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    # Try to like without auth
    response = await async_client.post(f"/api/v1/likes/{fake_id}")
    assert response.status_code == 401
    
    # Try to get likes without auth
    response = await async_client.get("/api/v1/likes/me")
    assert response.status_code == 401
    
    # Try to get stats without auth
    response = await async_client.get("/api/v1/likes/me/stats")
    assert response.status_code == 401
