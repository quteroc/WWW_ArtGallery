"""
Tests for the create_admin script.
"""
import pytest
from sqlalchemy import select
from app.models.user import User
from app.scripts.create_admin import create_or_promote_admin
from app.core.security import verify_password


@pytest.mark.asyncio
async def test_create_new_admin(db_session):
    """Test creating a new admin user."""
    # Create new admin
    result = await create_or_promote_admin(
        username="newadmin",
        email="newadmin@test.com",
        password="testpass123",
        db_session=db_session
    )
    
    assert result == 0
    
    # Verify user was created
    query = select(User).where(User.username == "newadmin")
    db_result = await db_session.execute(query)
    user = db_result.scalar_one_or_none()
    
    assert user is not None
    assert user.username == "newadmin"
    assert user.email == "newadmin@test.com"
    assert user.role == "admin"
    assert verify_password("testpass123", user.hashed_password)


@pytest.mark.asyncio
async def test_promote_existing_user_to_admin(db_session):
    """Test promoting an existing user to admin."""
    # Create a regular user first
    from app.core.security import get_password_hash
    from uuid import uuid4
    
    unique_username = f"regularuser_{uuid4().hex[:8]}"
    unique_email = f"regular_{uuid4().hex[:8]}@test.com"
    
    regular_user = User(
        username=unique_username,
        email=unique_email,
        hashed_password=get_password_hash("oldpass"),
        role="user"
    )
    db_session.add(regular_user)
    await db_session.commit()
    
    # Promote to admin without changing password
    result = await create_or_promote_admin(
        username=unique_username,
        email=unique_email,
        password=None,
        db_session=db_session
    )
    
    assert result == 0
    
    # Verify user was promoted
    query = select(User).where(User.username == unique_username)
    db_result = await db_session.execute(query)
    user = db_result.scalar_one_or_none()
    
    assert user is not None
    assert user.role == "admin"
    assert verify_password("oldpass", user.hashed_password)


@pytest.mark.asyncio
async def test_promote_and_update_password(db_session):
    """Test promoting a user and updating their password."""
    # Create a regular user first
    from app.core.security import get_password_hash
    from uuid import uuid4
    
    unique_username = f"usertochange_{uuid4().hex[:8]}"
    unique_email = f"change_{uuid4().hex[:8]}@test.com"
    
    regular_user = User(
        username=unique_username,
        email=unique_email,
        hashed_password=get_password_hash("oldpass"),
        role="user"
    )
    db_session.add(regular_user)
    await db_session.commit()
    
    # Promote to admin and change password
    result = await create_or_promote_admin(
        username=unique_username,
        email=unique_email,
        password="newpass456",
        db_session=db_session
    )
    
    assert result == 0
    
    # Verify user was promoted and password changed
    query = select(User).where(User.username == unique_username)
    db_result = await db_session.execute(query)
    user = db_result.scalar_one_or_none()
    
    assert user is not None
    assert user.role == "admin"
    assert verify_password("newpass456", user.hashed_password)
    assert not verify_password("oldpass", user.hashed_password)


@pytest.mark.asyncio
async def test_create_without_password_fails(db_session):
    """Test that creating a new user without a password fails."""
    result = await create_or_promote_admin(
        username="nopwduser",
        email="nopwd@test.com",
        password=None,
        db_session=db_session
    )
    
    assert result == 1
    
    # Verify user was not created
    query = select(User).where(User.username == "nopwduser")
    db_result = await db_session.execute(query)
    user = db_result.scalar_one_or_none()
    
    assert user is None
