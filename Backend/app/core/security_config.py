from typing import List, Dict
from pydantic import BaseModel
from app.core.config import settings


class SecurityConfig(BaseModel):
    """
    Centralized security configuration.
    """

    # Rate limiting settings
    GLOBAL_RATE_LIMIT: int = 100  # requests per minute
    LOGIN_RATE_LIMIT: int = 5  # attempts per 5 minutes
    API_KEY_CREATE_RATE_LIMIT: int = 10  # per hour
    PASSWORD_CHANGE_RATE_LIMIT: int = 3  # per hour

    # API Key settings
    MAX_API_KEYS_PER_USER: int = 10
    DEFAULT_API_KEY_EXPIRY_DAYS: int = 30
    MAX_API_KEY_EXPIRY_DAYS: int = 365

    # Request size limits
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Input validation limits
    MAX_STRING_LENGTH: int = 1000
    MAX_EMAIL_LENGTH: int = 254
    MAX_URL_LENGTH: int = 2048
    MAX_PHONE_LENGTH: int = 20
    MAX_COMPANY_NAME_LENGTH: int = 200
    MAX_SEARCH_QUERY_LENGTH: int = 500
    MIN_COMPANY_NAME_LENGTH: int = 2
    MIN_SEARCH_QUERY_LENGTH: int = 2

    # Security headers
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    # CORS settings
    DEVELOPMENT_CORS_ORIGINS: List[str] = ["*"]
    PRODUCTION_CORS_ORIGINS: List[str] = ["https://yourdomain.com"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # Allowed hosts for development
    DEVELOPMENT_ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # Paths that bypass rate limiting
    RATE_LIMIT_EXEMPT_PATHS: List[str] = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS: List[str] = [
        r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
        r"(union|select|insert|delete|update|drop|create|alter|exec|execute)",
        r"(script|javascript|vbscript|onload|onerror|onclick)",
    ]

    # XSS patterns
    XSS_PATTERNS: List[str] = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
    ]

    # Password requirements
    MIN_PASSWORD_LENGTH: int = 8
    MAX_PASSWORD_LENGTH: int = 128
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_NUMBERS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True

    # Session settings
    SESSION_TIMEOUT_MINUTES: int = 30
    REMEMBER_ME_DAYS: int = 30

    # Logging settings
    LOG_SECURITY_EVENTS: bool = True
    LOG_FAILED_LOGINS: bool = True
    LOG_RATE_LIMIT_VIOLATIONS: bool = True
    LOG_SUSPICIOUS_ACTIVITY: bool = True

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins based on environment."""
        if settings.ENVIRONMENT == "development":
            return self.DEVELOPMENT_CORS_ORIGINS
        return self.PRODUCTION_CORS_ORIGINS

    @property
    def allowed_hosts(self) -> List[str]:
        """Get allowed hosts based on environment."""
        if settings.ENVIRONMENT == "development":
            return self.DEVELOPMENT_ALLOWED_HOSTS
        return []

    @property
    def require_https(self) -> bool:
        """Whether HTTPS is required."""
        return settings.ENVIRONMENT == "production"


# Global security configuration instance
security_config = SecurityConfig()


# Permission definitions
class Permissions:
    """
    Define available permissions for API keys and users.
    """

    # Basic permissions
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

    # Specific resource permissions
    LEADS_READ = "leads:read"
    LEADS_WRITE = "leads:write"
    LEADS_DELETE = "leads:delete"

    SCRAPE_READ = "scrape:read"
    SCRAPE_WRITE = "scrape:write"
    SCRAPE_EXECUTE = "scrape:execute"

    ANALYTICS_READ = "analytics:read"

    EXPORT_READ = "export:read"
    EXPORT_EXECUTE = "export:execute"

    ADMIN = "admin"

    # Permission groups
    BASIC_PERMISSIONS = [READ]
    USER_PERMISSIONS = [READ, LEADS_READ, SCRAPE_READ, ANALYTICS_READ, EXPORT_READ]
    POWER_USER_PERMISSIONS = [
        READ,
        WRITE,
        LEADS_READ,
        LEADS_WRITE,
        SCRAPE_READ,
        SCRAPE_WRITE,
        SCRAPE_EXECUTE,
        ANALYTICS_READ,
        EXPORT_READ,
        EXPORT_EXECUTE,
    ]
    ADMIN_PERMISSIONS = [ADMIN]  # Admin has all permissions

    @classmethod
    def get_all_permissions(cls) -> List[str]:
        """Get all available permissions."""
        return [
            cls.READ,
            cls.WRITE,
            cls.DELETE,
            cls.LEADS_READ,
            cls.LEADS_WRITE,
            cls.LEADS_DELETE,
            cls.SCRAPE_READ,
            cls.SCRAPE_WRITE,
            cls.SCRAPE_EXECUTE,
            cls.ANALYTICS_READ,
            cls.EXPORT_READ,
            cls.EXPORT_EXECUTE,
            cls.ADMIN,
        ]

    @classmethod
    def validate_permissions(cls, permissions: List[str]) -> bool:
        """Validate that all permissions are valid."""
        valid_permissions = cls.get_all_permissions()
        return all(perm in valid_permissions for perm in permissions)


# Security event types
class SecurityEventTypes:
    """
    Define types of security events for logging.
    """

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"

    API_KEY_CREATED = "api_key_created"
    API_KEY_USED = "api_key_used"
    API_KEY_REVOKED = "api_key_revoked"

    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"

    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    PERMISSION_DENIED = "permission_denied"
    INVALID_INPUT = "invalid_input"

    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
