from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import get_supabase_client
from app.api.v1.api import api_router
from app.services.scheduler_service import get_scheduler_service
from app.core.security import SecurityMiddleware
from app.core.dependencies import check_rate_limit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Lead Generation SaaS Backend...")

    # Test Supabase connection
    try:
        # Simple test query to verify connection using schema_migrations table
        get_supabase_client().table("schema_migrations").select("*").limit(1).execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"⚠️ Supabase connection test failed: {e}")
        print("📝 Note: This is expected if tables don't exist yet")

    # Initialize and start scheduler service
    try:
        scheduler = get_scheduler_service()
        scheduler.start()
        print("✅ Scheduler service started successfully")
    except Exception as e:
        print(f"⚠️ Failed to start scheduler service: {e}")
        print("📝 Note: Monitoring tasks will not run automatically")

    yield

    # Shutdown
    print("🛑 Shutting down Lead Generation SaaS Backend...")

    # Stop scheduler service
    try:
        scheduler = get_scheduler_service()
        scheduler.stop()
        print("✅ Scheduler service stopped successfully")
    except Exception as e:
        print(f"⚠️ Failed to stop scheduler service: {e}")


app = FastAPI(
    title="Lead Generation SaaS Backend",
    description="A comprehensive lead generation system with web scraping and analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# Add security middleware
app.add_middleware(
    SecurityMiddleware,
    allowed_hosts=(
        ["localhost", "127.0.0.1", "0.0.0.0"]
        if settings.ENVIRONMENT == "development"
        else []
    ),
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if settings.ENVIRONMENT == "development" else ["https://yourdomain.com"]
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Global rate limiting middleware.
    """
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        response = await call_next(request)
        return response

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    try:
        await check_rate_limit(
            request, f"global:{client_ip}", limit=100, window=60
        )  # 100 requests per minute
        response = await call_next(request)
        return response
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            from app.core.security import SecurityLogger

            SecurityLogger.log_rate_limit_exceeded(request, client_ip)
        raise e


# Include API routes
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lead Generation SaaS Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
