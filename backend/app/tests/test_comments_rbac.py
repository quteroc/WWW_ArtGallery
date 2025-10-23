"""
Tests for comments API with role-based access control.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.artwork import Artwork
from app.models.category import Category
from app.models.comment import Comment
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
async def test_create_comment_success(
    async_client: AsyncClient,
    regular_user: User,
    test_artwork: Artwork
):
    """Test that authenticated users can create comments."""
    token = await get_token(async_client, regular_user)
    
    response = await async_client.post(
        f"/api/v1/comments/{test_artwork.id}",
        json={"content": "Great artwork!"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    comment = response.json()
    assert comment["content"] == "Great artwork!"
    assert comment["username"] == regular_user.username


@pytest.mark.asyncio
async def test_create_comment_requires_auth(
    async_client: AsyncClient,
    test_artwork: Artwork
):
    """Test that creating a comment requires authentication."""
    response = await async_client.post(
        f"/api/v1/comments/{test_artwork.id}",
        json={"content": "Test comment"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_comments(
    async_client: AsyncClient,
    test_artwork: Artwork
):
    """Test getting comments for an artwork."""
    response = await async_client.get(f"/api/v1/comments/{test_artwork.id}")
    
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)


@pytest.mark.asyncio
async def test_user_can_delete_own_comment(
    async_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    test_artwork: Artwork
):
    """Test that users can delete their own comments."""
    token = await get_token(async_client, regular_user)
    
    # Create a comment
    comment = Comment(
        user_id=regular_user.id,
        artwork_id=test_artwork.id,
        content="My comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    
    # Delete the comment
    response = await async_client.delete(
        f"/api/v1/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_manager_can_delete_any_comment(
    async_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    manager_user: User,
    test_artwork: Artwork
):
    """Test that managers can delete any comment (moderation)."""
    manager_token = await get_token(async_client, manager_user)
    
    # Create a comment as regular user
    comment = Comment(
        user_id=regular_user.id,
        artwork_id=test_artwork.id,
        content="User's comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    
    # Manager deletes the comment
    response = await async_client.delete(
        f"/api/v1/comments/{comment.id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_can_delete_any_comment(
    async_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    admin_user: User,
    test_artwork: Artwork
):
    """Test that admins can delete any comment."""
    admin_token = await get_token(async_client, admin_user)
    
    # Create a comment as regular user
    comment = Comment(
        user_id=regular_user.id,
        artwork_id=test_artwork.id,
        content="User's comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    
    # Admin deletes the comment
    response = await async_client.delete(
        f"/api/v1/comments/{comment.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_comment_requires_auth(
    async_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    test_artwork: Artwork
):
    """Test that deleting a comment requires authentication."""
    # Create a comment
    comment = Comment(
        user_id=regular_user.id,
        artwork_id=test_artwork.id,
        content="Test comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    
    # Try to delete without auth
    response = await async_client.delete(f"/api/v1/comments/{comment.id}")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_comment_nonexistent_artwork(
    async_client: AsyncClient,
    regular_user: User
):
    """Test creating comment for non-existent artwork."""
    from uuid import uuid4
    token = await get_token(async_client, regular_user)
    fake_id = uuid4()
    
    response = await async_client.post(
        f"/api/v1/comments/{fake_id}",
        json={"content": "Test comment"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_comment(
    async_client: AsyncClient,
    regular_user: User
):
    """Test deleting non-existent comment."""
    from uuid import uuid4
    token = await get_token(async_client, regular_user)
    fake_id = uuid4()
    
    response = await async_client.delete(
        f"/api/v1/comments/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
