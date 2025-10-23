"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.category import Category
from app.models.artwork import Artwork
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_register_login_success(async_client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration and login flow."""
    # Register a new user
    register_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = await async_client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["username"] == "testuser"
    assert data["role"] == "user"
    assert "id" in data
    
    # Login with the new user
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data  # OAuth2 uses form data, not JSON
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, db_session: AsyncSession):
    """Test login with invalid password."""
    # Create a user first
    user = User(
        email="user@example.com",
        username="testuser2",
        hashed_password=get_password_hash("correctpass"),
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Try to login with wrong password
    login_data = {
        "username": "testuser2",
        "password": "wrongpass"
    }
    
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_admin_protected_endpoint_requires_token(async_client: AsyncClient, db_session: AsyncSession):
    """Test that admin endpoints require authentication token."""
    # Create a category first
    category = Category(name="TestStyle", slug="test-style")
    db_session.add(category)
    await db_session.commit()
    
    # Try to create artwork without token
    artwork_data = {
        "title": "Test Artwork",
        "artist": "Test Artist",
        "style": "TestStyle",
        "image_path": "test.jpg",
        "popularity_score": 0.5
    }
    
    response = await async_client.post("/api/v1/artworks", json=artwork_data)
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_admin_protected_endpoint_requires_admin_role(async_client: AsyncClient, db_session: AsyncSession):
    """Test that admin endpoints require admin role."""
    # Create a category first
    category = Category(name="TestStyle2", slug="test-style-2")
    db_session.add(category)
    await db_session.commit()
    
    # Create a regular user (non-admin)
    user = User(
        email="regularuser@example.com",
        username="regularuser",
        hashed_password=get_password_hash("password123"),
        role="user"  # Not admin
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login as regular user
    login_data = {
        "username": "regularuser",
        "password": "password123"
    }
    
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Try to create artwork with user token (not admin)
    artwork_data = {
        "title": "Test Artwork",
        "artist": "Test Artist",
        "style": "TestStyle2",
        "image_path": "test.jpg",
        "popularity_score": 0.5
    }
    
    response = await async_client.post(
        "/api/v1/artworks",
        json=artwork_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403  # Forbidden (not admin)


@pytest.mark.asyncio
async def test_get_current_user_info(async_client: AsyncClient, db_session: AsyncSession):
    """Test getting current user information."""
    # Create a user
    user = User(
        email="infouser@example.com",
        username="infouser",
        hashed_password=get_password_hash("password123"),
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login
    login_data = {
        "username": "infouser",
        "password": "password123"
    }
    
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    
    # Get user info
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "infouser"
    assert data["email"] == "infouser@example.com"


@pytest.mark.asyncio
async def test_password_reset(async_client: AsyncClient, db_session: AsyncSession):
    """Test password reset functionality."""
    # Create a user
    user = User(
        email="resetuser@example.com",
        username="resetuser",
        hashed_password=get_password_hash("oldpassword"),
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login with old password
    login_data = {
        "username": "resetuser",
        "password": "oldpassword"
    }
    
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    
    # Reset password
    reset_data = {
        "old_password": "oldpassword",
        "new_password": "newpassword123"
    }
    
    response = await async_client.post(
        "/api/v1/auth/reset-password",
        json=reset_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Try to login with new password
    login_data = {
        "username": "resetuser",
        "password": "newpassword123"
    }
    
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    """Test registering with duplicate email."""
    # Register first user
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser1",
            "password": "password123"
        }
    )
    
    # Try to register with same email
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser2",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_username(async_client: AsyncClient):
    """Test registering with duplicate username."""
    # Register first user
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test1@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    
    # Try to register with same username
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
