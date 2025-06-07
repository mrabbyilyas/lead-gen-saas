from typing import List, Optional
import re
import html
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for adding security headers and basic protection.
    """

    def __init__(self, app, allowed_hosts: Optional[List[str]] = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or []

    async def dispatch(self, request: Request, call_next):
        # Check allowed hosts
        if self.allowed_hosts and request.headers.get("host") not in self.allowed_hosts:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Host not allowed"},
            )

        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class InputValidationError(Exception):
    """Custom exception for input validation errors"""

    pass


class InputValidator:
    """
    Input validation utilities for security.
    """

    # Common patterns for validation
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
    PHONE_PATTERN = re.compile(r"^[+]?[1-9]?[0-9]{7,15}$")

    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
        r"(union|select|insert|delete|update|drop|create|alter|exec|execute)",
        r"(script|javascript|vbscript|onload|onerror|onclick)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input by removing dangerous characters and limiting length.
        """
        if not isinstance(value, str):
            raise InputValidationError("Input must be a string")

        # Limit length
        if len(value) > max_length:
            raise InputValidationError(f"Input too long (max {max_length} characters)")

        # HTML escape
        value = html.escape(value)

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise InputValidationError("Potentially dangerous input detected")

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise InputValidationError("Potentially dangerous input detected")

        return value.strip()

    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email format.
        """
        email = cls.sanitize_string(email, 254)  # RFC 5321 limit

        if not cls.EMAIL_PATTERN.match(email):
            raise InputValidationError("Invalid email format")

        return email.lower()

    @classmethod
    def validate_url(cls, url: str) -> str:
        """
        Validate URL format.
        """
        url = cls.sanitize_string(url, 2048)  # Common URL length limit

        if not cls.URL_PATTERN.match(url):
            raise InputValidationError("Invalid URL format")

        return url

    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """
        Validate phone number format.
        """
        # Remove common separators
        phone = re.sub(r"[\s\-\(\)\.]", "", phone)
        phone = cls.sanitize_string(phone, 20)

        if not cls.PHONE_PATTERN.match(phone):
            raise InputValidationError("Invalid phone number format")

        return phone

    @classmethod
    def validate_company_name(cls, name: str) -> str:
        """
        Validate company name.
        """
        name = cls.sanitize_string(name, 200)

        if len(name) < 2:
            raise InputValidationError("Company name too short")

        # Allow letters, numbers, spaces, and common business characters
        if not re.match(r'^[a-zA-Z0-9\s\.,&\-\'"\(\)]+$', name):
            raise InputValidationError("Company name contains invalid characters")

        return name

    @classmethod
    def validate_search_query(cls, query: str) -> str:
        """
        Validate search query.
        """
        query = cls.sanitize_string(query, 500)

        if len(query) < 2:
            raise InputValidationError("Search query too short")

        return query


class SecurityLogger:
    """
    Security event logging.
    """

    @staticmethod
    def log_authentication_failure(request: Request, reason: str):
        """
        Log authentication failure.
        """
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.warning(
            f"Authentication failure: {reason} | "
            f"IP: {client_ip} | "
            f"User-Agent: {user_agent} | "
            f"Path: {request.url.path}"
        )

    @staticmethod
    def log_rate_limit_exceeded(request: Request, user_id: str):
        """
        Log rate limit exceeded.
        """
        client_ip = request.client.host if request.client else "unknown"

        logger.warning(
            f"Rate limit exceeded | "
            f"User: {user_id} | "
            f"IP: {client_ip} | "
            f"Path: {request.url.path}"
        )

    @staticmethod
    def log_suspicious_activity(request: Request, activity: str, details: str = ""):
        """
        Log suspicious activity.
        """
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.error(
            f"Suspicious activity: {activity} | "
            f"Details: {details} | "
            f"IP: {client_ip} | "
            f"User-Agent: {user_agent} | "
            f"Path: {request.url.path}"
        )


def validate_request_size(max_size: int = 10 * 1024 * 1024):  # 10MB default
    """
    Decorator to validate request content length.
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request too large",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_https(func):
    """
    Decorator to require HTTPS in production.
    """

    async def wrapper(request: Request, *args, **kwargs):
        from app.core.config import settings

        if settings.ENVIRONMENT == "production" and request.url.scheme != "https":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="HTTPS required"
            )
        return await func(request, *args, **kwargs)

    return wrapper
