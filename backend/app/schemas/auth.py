"""
Authentication schemas for API requests and responses.
"""
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login (OAuth2 password flow uses form data, this is for reference)."""
    username: str  # Can be email or username
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: UUID
    email: str
    username: str
    role: str
    is_active: bool


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    old_password: str
    new_password: str = Field(..., min_length=6)
