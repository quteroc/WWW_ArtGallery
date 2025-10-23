"""
Tests for categories endpoint.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category


@pytest.fixture
async def test_categories(db_session: AsyncSession):
    """Create test categories."""
    unique_id = uuid4().hex[:8]
    categories = [
        Category(name=f"Baroque{unique_id}", slug=f"baroque-{unique_id}"),
        Category(name=f"Renaissance{unique_id}", slug=f"renaissance-{unique_id}"),
        Category(name=f"Modern{unique_id}", slug=f"modern-{unique_id}"),
    ]
    for category in categories:
        db_session.add(category)
    await db_session.commit()
    
    for category in categories:
        await db_session.refresh(category)
    
    return categories


@pytest.mark.asyncio
async def test_list_categories(async_client: AsyncClient, test_categories):
    """Test listing all categories."""
    response = await async_client.get("/api/v1/categories")
    
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert len(categories) >= len(test_categories)


@pytest.mark.asyncio
async def test_categories_have_required_fields(async_client: AsyncClient, test_categories):
    """Test that categories have required fields."""
    response = await async_client.get("/api/v1/categories")
    
    assert response.status_code == 200
    categories = response.json()
    
    if len(categories) > 0:
        category = categories[0]
        assert "name" in category
        assert "slug" in category
