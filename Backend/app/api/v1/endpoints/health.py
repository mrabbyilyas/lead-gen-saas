"""Health check endpoints for monitoring system status."""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from app.core.dependencies import get_current_user, User
from app.services.monitoring_service import MonitoringService

# Create monitoring service instance
monitoring_service = MonitoringService()

router = APIRouter()


@router.get("/")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Lead Generation SaaS API",
        "version": "1.0.0",
    }


@router.get("/detailed")
def detailed_health_check():
    """Detailed health check with comprehensive system monitoring."""
    try:
        monitoring = monitoring_service
        health_data = monitoring.get_comprehensive_health()

        return {
            "status": health_data["status"],
            "timestamp": health_data["timestamp"],
            "service": "Lead Generation SaaS API",
            "version": health_data["version"],
            "environment": health_data["environment"],
            "health_score": health_data["overall_health_score"],
            "services": health_data["services"],
            "performance": health_data["performance"],
            "alerts": health_data["alerts"],
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/metrics")
def get_system_metrics(current_user: User = Depends(get_current_user)):
    """Get current system performance metrics and record them."""
    try:
        monitoring = monitoring_service

        # Get current performance
        performance = monitoring.get_system_performance()

        # Record metrics to database
        monitoring.record_performance_metrics()

        return {
            "timestamp": performance.timestamp.isoformat(),
            "performance": {
                "cpu_usage_percent": performance.cpu_usage_percent,
                "memory_usage_percent": performance.memory_usage_percent,
                "memory_available_gb": performance.memory_available_gb,
                "disk_usage_percent": performance.disk_usage_percent,
                "disk_free_gb": performance.disk_free_gb,
            },
            "status": "metrics_recorded",
        }

    except Exception as e:
        monitoring = monitoring_service
        monitoring.log_error(e, "get_system_metrics")
        raise HTTPException(
            status_code=500, detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/status")
def get_system_status(current_user: User = Depends(get_current_user)):
    """Get comprehensive system status including all services."""
    try:
        monitoring = monitoring_service
        return monitoring.get_comprehensive_health()

    except Exception as e:
        monitoring = monitoring_service
        monitoring.log_error(e, "get_system_status")
        raise HTTPException(
            status_code=500, detail=f"Failed to get system status: {str(e)}"
        )


@router.get("/trends")
def get_performance_trends(
    hours: int = Query(default=24, ge=1, le=168),  # 1 hour to 1 week
    current_user: User = Depends(get_current_user),
):
    """Get performance trends over the specified time period."""
    try:
        monitoring = monitoring_service
        trends = monitoring.get_performance_trends(hours=hours)

        return {"timestamp": datetime.utcnow().isoformat(), "trends": trends}

    except Exception as e:
        monitoring = monitoring_service
        monitoring.log_error(e, "get_performance_trends")
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance trends: {str(e)}"
        )


@router.get("/services")
def get_service_health(current_user: User = Depends(get_current_user)):
    """Get individual service health status."""
    try:
        monitoring = monitoring_service

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": monitoring.check_database_health().__dict__,
                "redis": monitoring.check_redis_health().__dict__,
                "celery": monitoring.check_celery_health().__dict__,
            },
        }

    except Exception as e:
        monitoring = monitoring_service
        monitoring.log_error(e, "get_service_health")
        raise HTTPException(
            status_code=500, detail=f"Failed to get service health: {str(e)}"
        )


@router.post("/record-metrics")
def record_current_metrics(current_user: User = Depends(get_current_user)):
    """Manually trigger recording of current performance metrics."""
    try:
        monitoring = monitoring_service
        monitoring.record_performance_metrics()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "metrics_recorded",
            "message": "Performance metrics have been recorded successfully",
        }

    except Exception as e:
        monitoring = monitoring_service
        monitoring.log_error(e, "record_current_metrics")
        raise HTTPException(
            status_code=500, detail=f"Failed to record metrics: {str(e)}"
        )
