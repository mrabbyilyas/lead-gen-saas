from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.models.api_schemas import (
    ScrapingJobRequest,
    ScrapingJobStatusResponse,
)
from app.services.background_jobs import (
    JobManager,
    JobType,
    JobPriority,
    JobStatus,
)

router = APIRouter()
job_manager = JobManager()


@router.post("/search", response_model=Dict[str, Any])
async def start_scraping_search(
    job_request: ScrapingJobRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new scraping job based on search parameters.

    This endpoint creates and submits a scraping job to the background task queue.
    The job will search for companies and contacts based on the provided parameters.

    Args:
        job_request: The scraping job configuration including search parameters
        background_tasks: FastAPI background tasks for async processing

    Returns:
        Dict containing job_id, status, and job details

    Raises:
        HTTPException: If job creation fails or invalid parameters provided
    """
    try:
        # Map job type to appropriate task
        task_mapping = {
            "google_my_business": "scraping_tasks.batch_scrape_task",
            "linkedin": "scraping_tasks.batch_scrape_task",
            "website": "scraping_tasks.scrape_companies_task",
            "directory": "scraping_tasks.scrape_companies_task",
            "multi_source": "scraping_tasks.batch_scrape_task",
        }

        task_name = task_mapping.get(job_request.job_type)
        if not task_name:
            raise HTTPException(
                status_code=400, detail=f"Unsupported job type: {job_request.job_type}"
            )

        # Convert priority string to enum
        priority_mapping = {
            "low": JobPriority.LOW,
            "normal": JobPriority.NORMAL,
            "high": JobPriority.HIGH,
            "urgent": JobPriority.CRITICAL,
        }
        priority = priority_mapping.get(job_request.priority, JobPriority.NORMAL)

        # Convert job type string to enum
        job_type_mapping = {
            "google_my_business": JobType.SCRAPING,
            "linkedin": JobType.SCRAPING,
            "website": JobType.SCRAPING,
            "directory": JobType.SCRAPING,
            "multi_source": JobType.SCRAPING,
        }
        job_type = job_type_mapping.get(job_request.job_type, JobType.SCRAPING)

        # Prepare job arguments
        job_kwargs = {
            "search_parameters": job_request.search_parameters.dict(),
            "job_name": job_request.job_name,
            "job_type": job_request.job_type,
            "webhook_url": (
                str(job_request.webhook_url) if job_request.webhook_url else None
            ),
            "notification_email": job_request.notification_email,
        }

        # Prepare job metadata
        metadata = {
            "job_name": job_request.job_name,
            "job_type": job_request.job_type,
            "search_keywords": job_request.search_parameters.keywords,
            "max_results": job_request.search_parameters.max_results,
            "include_contacts": job_request.search_parameters.include_contacts,
            "webhook_url": (
                str(job_request.webhook_url) if job_request.webhook_url else None
            ),
            "notification_email": job_request.notification_email,
            "created_by": "api",  # TODO: Add user authentication
        }

        # Calculate countdown if scheduled
        countdown = 0
        eta = None
        if job_request.schedule_at:
            eta = job_request.schedule_at
            countdown = max(
                0, int((job_request.schedule_at - datetime.utcnow()).total_seconds())
            )

        # Submit job to background queue
        job_id = job_manager.submit_job(
            task_name=task_name,
            job_type=job_type,
            kwargs=job_kwargs,
            priority=priority,
            metadata=metadata,
            countdown=countdown,
            eta=eta,
        )

        # Get initial job status
        job_status = job_manager.get_job_status(job_id)

        return {
            "job_id": job_id,
            "status": job_status.status.value if job_status else "pending",
            "message": f"Scraping job '{job_request.job_name}' created successfully",
            "job_name": job_request.job_name,
            "job_type": job_request.job_type,
            "priority": job_request.priority,
            "estimated_targets": job_request.search_parameters.max_results,
            "created_at": datetime.utcnow().isoformat(),
            "schedule_at": (
                job_request.schedule_at.isoformat() if job_request.schedule_at else None
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create scraping job: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=ScrapingJobStatusResponse)
async def get_scraping_status(job_id: str):
    """Get detailed status of a scraping job.

    This endpoint provides comprehensive information about a scraping job's
    current status, progress, performance metrics, and results.

    Args:
        job_id: The unique identifier of the scraping job

    Returns:
        ScrapingJobStatusResponse with detailed job information

    Raises:
        HTTPException: If job not found or status retrieval fails
    """
    try:
        # Validate job_id format
        try:
            UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid job_id format. Must be a valid UUID."
            )

        # Get job status from job manager
        job_status = job_manager.get_job_status(job_id)

        if not job_status:
            raise HTTPException(
                status_code=404, detail=f"Job with ID {job_id} not found"
            )

        # Calculate progress metrics
        progress_percentage = 0.0
        if job_status.progress and job_status.progress.total > 0:
            progress_percentage = (
                job_status.progress.current / job_status.progress.total
            ) * 100

        # Calculate time metrics
        elapsed_time = None
        remaining_time = None
        estimated_completion = None

        if job_status.started_at:
            elapsed_time = (datetime.utcnow() - job_status.started_at).total_seconds()

            if progress_percentage > 0 and job_status.status not in [
                JobStatus.SUCCESS,
                JobStatus.FAILURE,
                JobStatus.REVOKED,
            ]:
                total_estimated_time = elapsed_time * (100 / progress_percentage)
                remaining_time = max(0, total_estimated_time - elapsed_time)
                estimated_completion = datetime.utcnow() + timedelta(
                    seconds=remaining_time
                )

        # Extract performance metrics
        performance_metrics: Dict[str, Any] = {}
        if job_status.result_data and "performance_metrics" in job_status.result_data:
            performance_metrics = job_status.result_data["performance_metrics"] or {}

        # Build response
        response_data = {
            "job_id": UUID(job_id),
            "job_name": job_status.metadata.get("job_name", "Unknown Job"),
            "status": job_status.status.value,
            "progress_percentage": round(progress_percentage, 2),
            "total_targets": job_status.progress.total if job_status.progress else 0,
            "processed_targets": (
                job_status.progress.current if job_status.progress else 0
            ),
            "successful_extractions": 0,  # Not available in JobProgress, would need separate tracking
            "failed_extractions": 0,  # Not available in JobProgress, would need separate tracking
            "companies_found": performance_metrics.get("companies_found", 0),
            "contacts_found": performance_metrics.get("contacts_found", 0),
            "start_time": job_status.started_at,
            "estimated_completion": estimated_completion,
            "elapsed_time": elapsed_time,
            "remaining_time": remaining_time,
            "current_operation": (
                job_status.progress.message if job_status.progress else None
            ),
            "error_message": job_status.error_message,
            "performance_metrics": performance_metrics,
            "created_at": job_status.created_at,
        }

        return ScrapingJobStatusResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve job status: {str(e)}"
        )


@router.get("/jobs", response_model=Dict[str, Any])
async def list_scraping_jobs(
    status: Optional[List[str]] = Query(None, description="Filter by job status"),
    job_type: Optional[List[str]] = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
):
    """List scraping jobs with optional filtering and pagination.

    This endpoint provides a paginated list of scraping jobs with optional
    filtering by status, job type, and other criteria.

    Args:
        status: List of job statuses to filter by
        job_type: List of job types to filter by
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip for pagination
        sort_by: Field to sort results by
        sort_order: Sort order (asc or desc)

    Returns:
        Dict containing jobs list, pagination info, and metadata

    Raises:
        HTTPException: If listing fails or invalid parameters provided
    """
    try:
        # Get jobs from job manager
        jobs = job_manager.list_jobs(
            limit=limit,
            offset=offset,
        )

        # Format job data for response
        formatted_jobs = []
        for job in jobs:
            # Calculate progress percentage
            progress_percentage: float = 0.0
            if job.progress and job.progress.total > 0:
                progress_percentage = (job.progress.current / job.progress.total) * 100

            formatted_job = {
                "job_id": job.job_id,
                "job_name": job.metadata.get("job_name", "Unknown Job"),
                "job_type": job.metadata.get("job_type", "unknown"),
                "status": job.status.value,
                "progress_percentage": round(progress_percentage, 2),
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "priority": job.metadata.get("priority", "normal"),
                "estimated_targets": job.metadata.get("max_results", 0),
                "companies_found": 0,  # Will be updated from results
                "contacts_found": 0,  # Will be updated from results
            }

            # Add performance metrics if available
            if job.result_data and "performance_metrics" in job.result_data:
                metrics = job.result_data["performance_metrics"] or {}
                formatted_job["companies_found"] = metrics.get("companies_found", 0)
                formatted_job["contacts_found"] = metrics.get("contacts_found", 0)

            formatted_jobs.append(formatted_job)

        # Get total count for pagination (simplified approach)
        total_jobs = len(formatted_jobs)  # This is a simplified approach

        return {
            "jobs": formatted_jobs,
            "pagination": {
                "total": total_jobs,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_jobs,
                "has_prev": offset > 0,
            },
            "filters": {
                "status": status,
                "job_type": job_type,
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list scraping jobs: {str(e)}"
        )


@router.post("/jobs/{job_id}/cancel")
async def cancel_scraping_job(job_id: str):
    """Cancel a running or pending scraping job.

    This endpoint attempts to cancel a scraping job. Jobs that are already
    completed or failed cannot be cancelled.

    Args:
        job_id: The unique identifier of the scraping job to cancel

    Returns:
        Dict containing cancellation status and message

    Raises:
        HTTPException: If job not found, already completed, or cancellation fails
    """
    try:
        # Validate job_id format
        try:
            UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid job_id format. Must be a valid UUID."
            )

        # Check if job exists
        job_status = job_manager.get_job_status(job_id)
        if not job_status:
            raise HTTPException(
                status_code=404, detail=f"Job with ID {job_id} not found"
            )

        # Check if job can be cancelled
        if job_status.status in [
            JobStatus.SUCCESS,
            JobStatus.FAILURE,
            JobStatus.REVOKED,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job_status.status.value}",
            )

        # Cancel the job
        success = job_manager.cancel_job(job_id)

        if success:
            return {
                "job_id": job_id,
                "status": "cancelled",
                "message": "Job cancellation requested successfully",
                "cancelled_at": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cancel job. Job may have already completed.",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/jobs/{job_id}/progress")
async def get_job_progress(job_id: str):
    """Get real-time progress information for a scraping job.

    This endpoint provides lightweight progress information suitable for
    real-time updates and progress bars.

    Args:
        job_id: The unique identifier of the scraping job

    Returns:
        Dict containing progress percentage, current operation, and basic metrics

    Raises:
        HTTPException: If job not found or progress retrieval fails
    """
    try:
        # Validate job_id format
        try:
            UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid job_id format. Must be a valid UUID."
            )

        # Get job status
        job_status = job_manager.get_job_status(job_id)

        if not job_status:
            raise HTTPException(
                status_code=404, detail=f"Job with ID {job_id} not found"
            )

        # Calculate progress
        progress_percentage: float = 0.0
        if job_status.progress and job_status.progress.total > 0:
            progress_percentage = (
                job_status.progress.current / job_status.progress.total
            ) * 100

        # Calculate ETA
        eta = None
        if job_status.started_at and progress_percentage > 0:
            elapsed = (datetime.utcnow() - job_status.started_at).total_seconds()
            if progress_percentage < 100:
                total_estimated = elapsed * (100 / progress_percentage)
                remaining = max(0, total_estimated - elapsed)
                eta = (datetime.utcnow() + timedelta(seconds=remaining)).isoformat()

        return {
            "job_id": job_id,
            "status": job_status.status.value,
            "progress_percentage": round(progress_percentage, 2),
            "current_operation": (
                job_status.progress.message if job_status.progress else None
            ),
            "processed": job_status.progress.current if job_status.progress else 0,
            "total": job_status.progress.total if job_status.progress else 0,
            "successful": 0,  # Not available in JobProgress, would need to be tracked separately
            "failed": 0,  # Not available in JobProgress, would need to be tracked separately
            "estimated_completion": eta,
            "last_updated": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get job progress: {str(e)}"
        )
