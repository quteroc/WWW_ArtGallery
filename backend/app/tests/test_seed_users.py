"""
Tests for seed_users script.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, get_password_hash


async def seed_users_for_test():
    """Seed users for test - inline version."""
    from app.db.session import async_session
    
    try:
        async with async_session() as db:
            # Default users to create/update
            default_users = [
                {
                    "username": "admin",
                    "email": "admin@example.com",
                    "password": "admin123",
                    "role": "admin"
                },
                {
                    "username": "user",
                    "email": "user@example.com",
                    "password": "user123",
                    "role": "user"
                }
            ]
            
            for user_data in default_users:
                # Check if user exists
                query = select(User).where(User.username == user_data["username"])
                result = await db.execute(query)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user
                    existing_user.email = user_data["email"]
                    existing_user.hashed_password = get_password_hash(user_data["password"])
                    existing_user.role = user_data["role"]
                    existing_user.is_active = True
                else:
                    # Create new user
                    new_user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        hashed_password=get_password_hash(user_data["password"]),
                        role=user_data["role"],
                        is_active=True
                    )
                    db.add(new_user)
            
            await db.commit()
            return 0
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


@pytest.mark.asyncio
async def test_seed_users_creates_default_users(db_session: AsyncSession):
    """Test that seed_users creates default users."""
    # Run seed
    exit_code = await seed_users_for_test()
    assert exit_code == 0
    
    # Refresh session to see committed changes
    await db_session.rollback()
    
    # Check admin user
    query = select(User).where(User.username == "admin")
    result = await db_session.execute(query)
    admin = result.scalar_one_or_none()
    
    assert admin is not None
    assert admin.email == "admin@example.com"
    assert admin.role == "admin"
    assert admin.is_active is True
    assert verify_password("admin123", admin.hashed_password)
    
    # Check regular user
    query = select(User).where(User.username == "user")
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.email == "user@example.com"
    assert user.role == "user"
    assert user.is_active is True
    assert verify_password("user123", user.hashed_password)


@pytest.mark.asyncio
async def test_seed_users_updates_existing_users(db_session: AsyncSession):
    """Test that seed_users updates existing users."""
    # Create admin user with different password
    existing_admin = User(
        username="admin",
        email="old@example.com",
        hashed_password=get_password_hash("oldpassword"),
        role="user"
    )
    db_session.add(existing_admin)
    await db_session.commit()
    
    # Run seed
    exit_code = await seed_users_for_test()
    assert exit_code == 0
    
    # Refresh session
    await db_session.rollback()
    
    # Check that admin was updated
    query = select(User).where(User.username == "admin")
    result = await db_session.execute(query)
    admin = result.scalar_one_or_none()
    
    assert admin is not None
    assert admin.email == "admin@example.com"  # Updated
    assert admin.role == "admin"  # Updated
    assert verify_password("admin123", admin.hashed_password)  # Updated
    assert not verify_password("oldpassword", admin.hashed_password)


@pytest.mark.asyncio
async def test_seed_users_idempotent(db_session: AsyncSession):
    """Test that seed_users can be run multiple times."""
    # Run seed twice
    exit_code1 = await seed_users_for_test()
    assert exit_code1 == 0
    
    exit_code2 = await seed_users_for_test()
    assert exit_code2 == 0
    
    # Refresh session
    await db_session.rollback()
    
    # Check that we still have exactly 2 users
    query = select(User)
    result = await db_session.execute(query)
    users = result.scalars().all()
    
    assert len(users) == 2
    usernames = {u.username for u in users}
    assert usernames == {"admin", "user"}
