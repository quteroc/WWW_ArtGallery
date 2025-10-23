"""
Tests for manager role permissions vs admin role.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.artwork import Artwork
from app.models.category import Category
from app.core.security import get_password_hash


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
async def regular_user(db_session: AsyncSession) -> User:
    """Create a regular user."""
    unique_id = uuid4().hex[:8]
    user = User(
        email=f"user{unique_id}@example.com",
        username=f"user{unique_id}",
        hashed_password=get_password_hash("password123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager_user(db_session: AsyncSession) -> User:
    """Create a manager user."""
    unique_id = uuid4().hex[:8]
    user = User(
        email=f"manager{unique_id}@example.com",
        username=f"manager{unique_id}",
        hashed_password=get_password_hash("password123"),
        role="manager",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    unique_id = uuid4().hex[:8]
    user = User(
        email=f"admin{unique_id}@example.com",
        username=f"admin{unique_id}",
        hashed_password=get_password_hash("password123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_artwork(db_session: AsyncSession, test_category: Category) -> Artwork:
    """Create a test artwork."""
    artwork = Artwork(
        title="Test Artwork",
        artist="Test Artist",
        style=test_category.name,
        image_path=f"{test_category.name}/test.jpg",
        image_url=f"https://example.com/{test_category.name}/test.jpg",
        popularity_score=5.0,
        is_active=True
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    return artwork


async def get_token(async_client: AsyncClient, user: User) -> str:
    """Get auth token for a user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_manager_can_toggle_artwork_active(
    async_client: AsyncClient,
    manager_user: User,
    test_artwork: Artwork
):
    """Test that managers can toggle artwork active status."""
    token = await get_token(async_client, manager_user)
    
    response = await async_client.post(
        f"/api/v1/artworks/{test_artwork.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    artwork = response.json()
    # Should be toggled
    assert artwork["is_active"] != test_artwork.is_active


@pytest.mark.asyncio
async def test_manager_cannot_delete_artwork(
    async_client: AsyncClient,
    manager_user: User,
    test_artwork: Artwork
):
    """Test that managers cannot delete artworks (admin only)."""
    token = await get_token(async_client, manager_user)
    
    response = await async_client.delete(
        f"/api/v1/artworks/{test_artwork.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_admin_can_delete_artwork(
    async_client: AsyncClient,
    admin_user: User,
    test_artwork: Artwork
):
    """Test that admins can delete artworks."""
    token = await get_token(async_client, admin_user)
    
    response = await async_client.delete(
        f"/api/v1/artworks/{test_artwork.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user_cannot_toggle_artwork(
    async_client: AsyncClient,
    regular_user: User,
    test_artwork: Artwork
):
    """Test that regular users cannot toggle artwork status."""
    token = await get_token(async_client, regular_user)
    
    response = await async_client.post(
        f"/api/v1/artworks/{test_artwork.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_manager_cannot_create_artwork(
    async_client: AsyncClient,
    manager_user: User,
    test_category: Category
):
    """Test that managers cannot create artworks (admin only)."""
    token = await get_token(async_client, manager_user)
    
    response = await async_client.post(
        "/api/v1/artworks",
        json={
            "title": "New Artwork",
            "artist": "New Artist",
            "style": test_category.name,
            "image_path": f"{test_category.name}/new.jpg",
            "popularity_score": 5.0,
            "is_active": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_artwork(
    async_client: AsyncClient,
    admin_user: User,
    test_category: Category
):
    """Test that admins can create artworks."""
    token = await get_token(async_client, admin_user)
    
    response = await async_client.post(
        "/api/v1/artworks",
        json={
            "title": "New Artwork",
            "artist": "New Artist",
            "style": test_category.name,
            "image_path": f"{test_category.name}/new.jpg",
            "popularity_score": 5.0,
            "is_active": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    artwork = response.json()
    assert artwork["title"] == "New Artwork"
