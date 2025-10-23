"""
Tests for password reset functionality.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import get_password_hash, verify_password


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    unique_id = uuid4().hex[:8]
    user = User(
        email=f"testuser{unique_id}@example.com",
        username=f"testuser{unique_id}",
        hashed_password=get_password_hash("oldpassword123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_password_reset_success(
    async_client: AsyncClient,
    test_user: User
):
    """Test successful password reset."""
    # Login with old password
    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.username, "password": "oldpassword123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Reset password
    reset_response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={
            "old_password": "oldpassword123",
            "new_password": "newpassword456"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert reset_response.status_code == 200
    
    # Try login with new password
    new_login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.username, "password": "newpassword456"}
    )
    assert new_login_response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_wrong_old_password(
    async_client: AsyncClient,
    test_user: User
):
    """Test password reset with wrong old password."""
    # Login
    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.username, "password": "oldpassword123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Try to reset with wrong old password
    reset_response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={
            "old_password": "wrongpassword",
            "new_password": "newpassword456"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert reset_response.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_requires_auth(async_client: AsyncClient):
    """Test that password reset requires authentication."""
    response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={
            "old_password": "oldpassword123",
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 401
