from fastapi import APIRouter, HTTPException
from app.core.database import test_database_connection
from app.core.config import settings
import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including database connectivity"""

    # Test database connection
    db_status = "healthy" if test_database_connection() else "unhealthy"

    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": {"status": db_status, "type": "supabase"},
            "redis": {
                "status": "unknown",  # Will implement Redis check later
                "url": settings.REDIS_URL,
            },
        },
    }

    if health_data["status"] == "degraded":
        raise HTTPException(status_code=503, detail=health_data)

    return health_data
