"""
Tests for admin artwork operations.
"""
import pytest
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.category import Category
from app.models.artwork import Artwork
from app.core.security import get_password_hash


async def create_admin_user(db_session: AsyncSession):
    """Helper to create an admin user."""
    from uuid import uuid4
    unique_id = uuid4().hex[:8]
    admin = User(
        email=f"admin{unique_id}@example.com",
        username=f"admin{unique_id}",
        hashed_password=get_password_hash("adminpass"),
        role="admin"
    )
    db_session.add(admin)
    await db_session.commit()
    return admin


async def get_admin_token(async_client: AsyncClient, admin: User):
    """Helper to get admin auth token."""
    login_data = {
        "username": admin.username,
        "password": "adminpass"
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_artwork_as_admin(async_client: AsyncClient, db_session: AsyncSession):
    """Test creating artwork as admin."""
    from uuid import uuid4
    unique_id = uuid4().hex[:8]
    
    # Create admin user and category
    admin = await create_admin_user(db_session)
    category = Category(name=f"AdminTestStyle{unique_id}", slug=f"admin-test-style-{unique_id}")
    db_session.add(category)
    await db_session.commit()
    
    # Get admin token
    token = await get_admin_token(async_client, admin)
    
    # Create artwork
    artwork_data = {
        "title": "Admin Created Artwork",
        "artist": "Admin Artist",
        "style": category.name,
        "image_path": "ml/input/wikiart/AdminTestStyle/test.jpg",
        "popularity_score": 0.8,
        "is_active": True
    }
    
    response = await async_client.post(
        "/api/v1/artworks",
        json=artwork_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Admin Created Artwork"
    assert data["artist"] == "Admin Artist"
    assert data["is_active"] is True
    # Image URL should now use CDN base URL
    from app.core.config import settings
    assert settings.ARTWORKS_BASE_URL in data["image_url"]


@pytest.mark.asyncio
async def test_update_artwork_as_admin(async_client: AsyncClient, db_session: AsyncSession):
    """Test updating artwork as admin."""
    # Setup
    await create_admin_user(db_session)
    category = Category(name="UpdateTestStyle", slug="update-test-style")
    db_session.add(category)
    await db_session.commit()
    
    artwork = Artwork(
        title="Original Title",
        artist="Original Artist",
        style="UpdateTestStyle",
        image_path="test.jpg",
        image_url="/static/artworks/test.jpg"
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    
    # Get admin token
    token = await get_admin_token(async_client)
    
    # Update artwork
    update_data = {
        "title": "Updated Title",
        "popularity_score": 0.95
    }
    
    response = await async_client.put(
        f"/api/v1/artworks/{artwork.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["popularity_score"] == 0.95


@pytest.mark.asyncio
async def test_delete_artwork_as_admin(async_client: AsyncClient, db_session: AsyncSession):
    """Test soft-deleting artwork as admin."""
    # Setup
    await create_admin_user(db_session)
    category = Category(name="DeleteTestStyle", slug="delete-test-style")
    db_session.add(category)
    await db_session.commit()
    
    artwork = Artwork(
        title="To Be Deleted",
        artist="Delete Artist",
        style="DeleteTestStyle",
        image_path="test.jpg",
        image_url="/static/artworks/test.jpg",
        is_active=True
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    
    # Get admin token
    token = await get_admin_token(async_client)
    
    # Delete artwork
    response = await async_client.delete(
        f"/api/v1/artworks/{artwork.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Verify artwork is soft-deleted (is_active = False)
    from sqlalchemy import select
    query = select(Artwork).where(Artwork.id == artwork.id)
    result = await db_session.execute(query)
    deleted_artwork = result.scalar_one_or_none()
    assert deleted_artwork is not None
    assert deleted_artwork.is_active is False


@pytest.mark.asyncio
async def test_toggle_artwork_active(async_client: AsyncClient, db_session: AsyncSession):
    """Test toggling artwork active status."""
    # Setup
    await create_admin_user(db_session)
    category = Category(name="ToggleTestStyle", slug="toggle-test-style")
    db_session.add(category)
    await db_session.commit()
    
    artwork = Artwork(
        title="Toggle Test",
        artist="Toggle Artist",
        style="ToggleTestStyle",
        image_path="test.jpg",
        image_url="/static/artworks/test.jpg",
        is_active=True
    )
    db_session.add(artwork)
    await db_session.commit()
    await db_session.refresh(artwork)
    
    # Get admin token
    token = await get_admin_token(async_client)
    
    # Toggle to inactive
    response = await async_client.post(
        f"/api/v1/artworks/{artwork.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    
    # Toggle back to active
    response = await async_client.post(
        f"/api/v1/artworks/{artwork.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_import_artwork_from_path_file_not_found(async_client: AsyncClient, db_session: AsyncSession):
    """Test import-from-path with non-existent file."""
    # Setup
    await create_admin_user(db_session)
    category = Category(name="ImportTestStyle", slug="import-test-style")
    db_session.add(category)
    await db_session.commit()
    
    # Get admin token
    token = await get_admin_token(async_client)
    
    # Try to import non-existent file
    import_data = {
        "image_path": "ml/input/wikiart/ImportTestStyle/nonexistent.jpg"
    }
    
    response = await async_client.post(
        "/api/v1/artworks/import-from-path",
        json=import_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "File not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_import_artwork_from_path_with_parsing(async_client: AsyncClient, db_session: AsyncSession):
    """Test import-from-path with filename parsing."""
    # Setup
    await create_admin_user(db_session)
    category = Category(name="Baroque", slug="baroque")
    db_session.add(category)
    await db_session.commit()
    
    # Create a temporary test file
    test_dir = "/tmp/test_wikiart/Baroque"
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "rembrandt-night_watch.jpg")
    with open(test_file, "w") as f:
        f.write("test")
    
    # Get admin token
    token = await get_admin_token(async_client)
    
    # Import artwork (style inferred from path, title/artist from filename)
    import_data = {
        "image_path": f"{test_dir}/rembrandt-night_watch.jpg"
    }
    
    response = await async_client.post(
        "/api/v1/artworks/import-from-path",
        json=import_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Clean up
    os.remove(test_file)
    
    assert response.status_code == 200
    data = response.json()
    assert data["artist"] == "Rembrandt"
    assert data["title"] == "Night Watch"
    # Note: Style won't be "Baroque" because the path doesn't match ml/input/wikiart pattern
    assert data["is_active"] is True
