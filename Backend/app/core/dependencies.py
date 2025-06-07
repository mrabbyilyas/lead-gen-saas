from typing import Optional, Dict, List
from datetime import datetime
import hashlib
import secrets
import time
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel
import redis
from app.core.config import settings

# Security schemes
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting storage (Redis)
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None


class User(BaseModel):
    """User model for authentication"""

    id: str
    email: str
    is_active: bool = True
    is_admin: bool = False
    api_key: Optional[str] = None
    rate_limit: int = 60  # requests per minute


class APIKey(BaseModel):
    """API Key model"""

    id: Optional[str] = None
    key: str
    key_hash: Optional[str] = None
    user_id: str
    name: str
    is_active: bool = True
    rate_limit: int = 60
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    permissions: List[str] = []


# In-memory API key storage (in production, use database)
API_KEYS_STORE: Dict[str, APIKey] = {
    "sk-dev-12345678901234567890123456789012": APIKey(
        key="sk-dev-12345678901234567890123456789012",
        user_id="00000000-0000-0000-0000-000000000000",
        name="Development Key",
        rate_limit=1000,
        created_at=datetime.utcnow(),
    )
}

# Alias for backward compatibility
API_KEYS: Dict[str, APIKey] = API_KEYS_STORE


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"sk-{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def check_rate_limit(
    request: Request, key: str, limit: int = 60, window: int = 60
) -> bool:
    """
    Check if user has exceeded rate limit.
    Returns True if within limit, False if exceeded.
    """
    if not redis_client:
        return True  # Allow if Redis is not available

    current_time = int(time.time())
    window_start = current_time - 60  # 1-minute window

    redis_key = f"rate_limit:{key}"

    try:
        # Remove old entries
        await redis_client.zremrangebyscore(redis_key, 0, window_start)

        # Count current requests
        current_count = await redis_client.zcard(redis_key)

        if current_count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

        # Add current request
        await redis_client.zadd(redis_key, {str(current_time): current_time})
        await redis_client.expire(redis_key, window)  # Expire after 1 minute

        return True
    except Exception:
        return True  # Allow if Redis operation fails


async def get_current_user_from_api_key(
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[User]:
    """
    Get current user from API key.
    """
    if not api_key:
        return None

    # Check if API key exists and is valid
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    api_key_obj = API_KEYS[api_key]

    # Check if API key is active
    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is disabled"
        )

    # Check if API key has expired
    if api_key_obj.expires_at and datetime.utcnow() > api_key_obj.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key has expired"
        )

    # Check rate limit (create a mock request for rate limiting)
    from fastapi import Request

    mock_request = Request({"type": "http", "method": "GET", "url": "/", "headers": []})
    try:
        await check_rate_limit(
            mock_request, f"api_key:{api_key_obj.user_id}", api_key_obj.rate_limit
        )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )

    # Update last used timestamp
    api_key_obj.last_used = datetime.utcnow()

    # Return user associated with API key
    return User(
        id=api_key_obj.user_id,
        email="api@example.com",
        is_active=True,
        is_admin=True,
        api_key=api_key,
        rate_limit=api_key_obj.rate_limit,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    """
    Get current user from authentication token or API key.
    Priority: API Key > Bearer Token > Development Default
    """
    # First, try API key authentication
    if api_user:
        return api_user

    # Then try Bearer token authentication
    if credentials:
        token = credentials.credentials
        # TODO: Implement proper JWT token validation
        # For now, accept any token for development
        return User(
            id="00000000-0000-0000-0000-000000000001",
            email="bearer@example.com",
            is_active=True,
            is_admin=False,
        )

    # Development mode: allow unauthenticated access
    if settings.ENVIRONMENT == "development":
        return User(
            id="00000000-0000-0000-0000-000000000000",
            email="dev@example.com",
            is_active=True,
            is_admin=True,
        )

    # Production: require authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current admin user.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Dependency to check if the current user has the required permissions.
    """

    def check_permissions(current_user: User = Depends(get_current_user)):
        # For development, allow all permissions for admin user
        if current_user.email == "admin@example.com":
            return None

        # TODO: Implement proper permission checking
        # This should check user's role and permissions against required_permissions
        # For now, we'll allow all authenticated users
        return None

    return check_permissions
