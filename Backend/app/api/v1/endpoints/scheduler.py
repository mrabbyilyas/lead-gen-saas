"""Scheduler management endpoints for monitoring scheduled tasks."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_current_user, User
from app.services.scheduler_service import get_scheduler_service

router = APIRouter()


class JobResponse(BaseModel):
    """Response model for scheduled job information."""

    id: str
    name: str
    next_run: Optional[str] = None
    trigger: str
    func_name: str


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""

    scheduler_running: bool
    total_jobs: int
    jobs: List[JobResponse]


@router.get("/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """Get the current status of the scheduler and all scheduled jobs."""
    try:
        scheduler = get_scheduler_service()
        status = scheduler.get_job_status()

        return SchedulerStatusResponse(
            scheduler_running=status["scheduler_running"],
            total_jobs=status["total_jobs"],
            jobs=[
                JobResponse(
                    id=job["id"],
                    name=job["name"],
                    next_run=job["next_run"],
                    trigger=job["trigger"],
                    func_name=job["func_name"],
                )
                for job in status["jobs"]
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.post("/start")
def start_scheduler(current_user: User = Depends(get_current_user)):
    """Start the scheduler service."""
    try:
        scheduler = get_scheduler_service()
        scheduler.start()

        return {
            "message": "Scheduler started successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start scheduler: {str(e)}"
        )


@router.post("/stop")
def stop_scheduler(current_user: User = Depends(get_current_user)):
    """Stop the scheduler service."""
    try:
        scheduler = get_scheduler_service()
        scheduler.stop()

        return {
            "message": "Scheduler stopped successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "stopped",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop scheduler: {str(e)}"
        )


@router.get("/jobs")
def list_scheduled_jobs(current_user: User = Depends(get_current_user)):
    """List all scheduled jobs with their details."""
    try:
        scheduler = get_scheduler_service()
        status = scheduler.get_job_status()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "scheduler_running": status["scheduler_running"],
            "total_jobs": status["total_jobs"],
            "jobs": status["jobs"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list scheduled jobs: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
def remove_scheduled_job(job_id: str, current_user: User = Depends(get_current_user)):
    """Remove a specific scheduled job."""
    try:
        scheduler = get_scheduler_service()
        scheduler.remove_job(job_id)

        return {
            "message": f"Job '{job_id}' removed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove job '{job_id}': {str(e)}"
        )


@router.get("/health")
def scheduler_health_check(current_user: User = Depends(get_current_user)):
    """Check the health of the scheduler service."""
    try:
        scheduler = get_scheduler_service()
        status = scheduler.get_job_status()

        # Determine health status
        is_healthy = status["scheduler_running"] and status["total_jobs"] > 0

        health_status = {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "scheduler_running": status["scheduler_running"],
            "total_jobs": status["total_jobs"],
            "details": {
                "message": (
                    "Scheduler is running with scheduled jobs"
                    if is_healthy
                    else "Scheduler is not running or has no jobs"
                ),
                "job_count": status["total_jobs"],
            },
        }

        return health_status

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "details": {"message": "Failed to check scheduler health"},
        }
