"""
User authentication models for multi-tenant SaaS.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
from typing import Optional
import uuid


class User(BaseModel):
    """
    User account model.
    
    Fields:
        id: Unique user ID (UUID)
        email: User email (used for login)
        password_hash: Bcrypt hashed password
        full_name: User's full name
        email_verified: Email verification status
        created_at: Account creation timestamp
        last_login: Last login timestamp
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    full_name: Optional[str] = None
    email_verified: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    active: bool = True


class UserCreate(BaseModel):
    """
    User signup request.
    """
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """
    User login request.
    """
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Public user data (no password hash).
    """
    id: str
    email: EmailStr
    full_name: Optional[str]
    email_verified: bool
    created_at: str
    last_login: Optional[str]


class TokenResponse(BaseModel):
    """
    Authentication response with JWT token.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
