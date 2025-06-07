from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)

class User(BaseModel):
    """User model for authentication"""
    id: str
    email: str
    is_active: bool = True
    is_admin: bool = False

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current user from authentication token.
    
    For now, this is a placeholder implementation that returns a default user.
    In a production environment, this should:
    1. Validate the JWT token
    2. Extract user information from the token
    3. Verify user exists and is active
    4. Return the authenticated user
    """
    # TODO: Implement proper JWT token validation
    # For now, return a default admin user for development
    if credentials is None:
        # Allow unauthenticated access for development
        return User(
            id="00000000-0000-0000-0000-000000000000",
            email="admin@example.com",
            is_active=True,
            is_admin=True
        )
    
    # In production, validate the token here
    token = credentials.credentials
    
    # Placeholder validation - accept any token for development
    return User(
        id="00000000-0000-0000-0000-000000000000",
        email="admin@example.com",
        is_active=True,
        is_admin=True
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user