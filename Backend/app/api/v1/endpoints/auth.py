from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from app.core.dependencies import (
    get_current_active_user,
    generate_api_key,
    hash_api_key,
    check_rate_limit,
    API_KEYS_STORE,
    User,
)
from app.core.security import SecurityLogger, InputValidator
import secrets

router = APIRouter()
security = HTTPBearer()


class APIKeyCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Name for the API key"
    )
    expires_days: Optional[int] = Field(
        30, ge=1, le=365, description="Days until expiration (1-365)"
    )
    permissions: List[str] = Field(
        default=["read"], description="Permissions for the API key"
    )


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only returned on creation
    created_at: datetime
    expires_at: Optional[datetime]
    permissions: List[str]
    is_active: bool


class APIKeyInfo(BaseModel):
    id: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    permissions: List[str]
    is_active: bool
    last_used: Optional[datetime]


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


@router.post("/login", response_model=dict)
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return access token.
    Note: This is a placeholder implementation.
    """
    try:
        # Rate limiting for login attempts
        client_ip = request.client.host if request.client else "unknown"
        await check_rate_limit(
            request, f"login:{client_ip}", limit=5, window=300
        )  # 5 attempts per 5 minutes

        # Validate input
        email = InputValidator.validate_email(login_data.email)

        # TODO: Implement actual authentication logic
        # This should verify credentials against your user database

        # For now, return a placeholder response
        SecurityLogger.log_authentication_failure(
            request, "Login endpoint not fully implemented"
        )

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Login endpoint not yet implemented. Use API key authentication.",
        )

    except Exception as e:
        SecurityLogger.log_authentication_failure(request, str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: Request,
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new API key for the authenticated user.
    """
    try:
        # Rate limiting for API key creation
        await check_rate_limit(
            request, f"api_key_create:{current_user.id}", limit=10, window=3600
        )  # 10 per hour

        # Validate input
        name = InputValidator.sanitize_string(api_key_data.name, 100)

        # Check if user already has too many API keys
        user_keys = [
            key
            for key in API_KEYS_STORE.values()
            if key.user_id == current_user.id and key.is_active
        ]
        if len(user_keys) >= 10:  # Limit to 10 active keys per user
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of API keys reached (10)",
            )

        # Generate new API key
        api_key = generate_api_key()
        key_id = secrets.token_urlsafe(16)

        # Calculate expiration
        expires_at = None
        if api_key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_days)

        # Store API key
        from app.core.dependencies import APIKey

        api_key_obj = APIKey(
            id=key_id,
            key=api_key,
            user_id=current_user.id,
            name=name,
            key_hash=hash_api_key(api_key),
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            permissions=api_key_data.permissions,
            is_active=True,
        )

        API_KEYS_STORE[key_id] = api_key_obj

        return APIKeyResponse(
            id=key_id,
            name=name,
            key=api_key,  # Only returned on creation
            created_at=api_key_obj.created_at,
            expires_at=expires_at,
            permissions=api_key_data.permissions,
            is_active=True,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.get("/api-keys", response_model=List[APIKeyInfo])
async def list_api_keys(current_user: User = Depends(get_current_active_user)):
    """
    List all API keys for the authenticated user.
    """
    user_keys = [
        APIKeyInfo(
            id=key.id or "",
            name=key.name,
            created_at=key.created_at,
            expires_at=key.expires_at,
            permissions=key.permissions,
            is_active=key.is_active,
            last_used=key.last_used,
        )
        for key in API_KEYS_STORE.values()
        if key.user_id == current_user.id
    ]

    return user_keys


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Revoke an API key.
    """
    # Find the API key
    api_key = API_KEYS_STORE.get(key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # Check ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this API key",
        )

    # Revoke the key
    api_key.is_active = False

    return {"message": "API key revoked successfully"}


@router.put("/api-keys/{key_id}")
async def update_api_key(
    key_id: str,
    name: str = Field(..., min_length=1, max_length=100),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an API key's name.
    """
    # Find the API key
    api_key = API_KEYS_STORE.get(key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # Check ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this API key",
        )

    # Validate and update name
    api_key.name = InputValidator.sanitize_string(name, 100)

    return {"message": "API key updated successfully"}


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Change user password.
    Note: This is a placeholder implementation.
    """
    try:
        # Rate limiting for password changes
        await check_rate_limit(
            request, f"password_change:{current_user.id}", limit=3, window=3600
        )  # 3 per hour

        # TODO: Implement actual password change logic
        # This should verify current password and update with new password

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Password change not yet implemented",
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    """
    return current_user


@router.get("/security-log")
async def get_security_events(
    current_user: User = Depends(get_current_active_user),
    limit: int = Field(50, ge=1, le=100),
):
    """
    Get recent security events for the user.
    Note: This is a placeholder implementation.
    """
    # TODO: Implement actual security log retrieval
    # This should return recent login attempts, API key usage, etc.

    return {"message": "Security log endpoint not yet implemented", "events": []}
