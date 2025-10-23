"""
API dependencies for FastAPI routes.
"""
from typing import AsyncGenerator, List, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import async_session
from app.core.security import decode_access_token
from app.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with async_session() as session:
        yield session


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object (for cookie access)
        token: JWT access token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from Authorization header first, then from cookie
    if token is None:
        token = request.cookies.get("access_token")
    
    # Check if token was provided
    if token is None:
        raise credentials_exception
    
    # Decode token
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: List of roles that are allowed to access the endpoint
        
    Returns:
        Dependency function that checks user role
        
    Example:
        @router.post("/admin-only", dependencies=[Depends(require_roles("admin"))])
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token, or None if not authenticated.
    
    This is a non-raising version of get_current_user for web pages that
    should work both authenticated and unauthenticated.
    
    Args:
        request: FastAPI request object (for cookie access)
        token: JWT access token from Authorization header (optional)
        db: Database session
        
    Returns:
        Current authenticated user or None
    """
    # Try to get token from Authorization header first, then from cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    # Decode token
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    
    # Get user from database
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        return None
    
    return user
