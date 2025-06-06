"""Job manager for handling background job lifecycle and tracking."""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from celery import current_app
from celery.result import AsyncResult
import redis

from app.core.config import settings
from .job_status import JobStatus, JobType, JobPriority, JobResult, JobProgress


class JobManager:
    """Manages background job lifecycle and tracking."""

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.celery_app = current_app
        self.job_prefix = "job:"
        self.job_list_key = "jobs:active"
        self.job_stats_key = "jobs:stats"

    def submit_job(
        self,
        task_name: str,
        job_type: JobType,
        args: tuple = (),
        kwargs: Optional[Dict[Any, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[Any, Any]] = None,
        countdown: int = 0,
        eta: Optional[datetime] = None,
    ) -> str:
        """Submit a new background job."""
        kwargs = kwargs or {}
        metadata = metadata or {}

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create job result object
        job_result = JobResult(
            job_id=job_id,
            status=JobStatus.PENDING,
            job_type=job_type,
            created_at=datetime.utcnow(),
            metadata=metadata,
        )

        # Store job info in Redis
        self._store_job_result(job_result)

        # Submit to Celery with custom job ID
        celery_result = self.celery_app.send_task(
            task_name,
            args=args,
            kwargs=kwargs,
            task_id=job_id,
            priority=priority.value,
            countdown=countdown,
            eta=eta,
        )

        # Add to active jobs list
        self.redis_client.sadd(self.job_list_key, job_id)

        # Update statistics
        self._update_job_stats("submitted", job_type)

        return job_id

    def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """Get current status of a job."""
        # First check Redis cache
        cached_result = self._get_job_result(job_id)
        if cached_result and cached_result.is_completed:
            return cached_result

        # Check Celery result
        celery_result = AsyncResult(job_id, app=self.celery_app)

        if cached_result:
            # Update from Celery if job is still running
            cached_result.status = JobStatus(celery_result.status.lower())

            if celery_result.info and isinstance(celery_result.info, dict):
                if "progress" in celery_result.info:
                    progress_data = celery_result.info["progress"]
                    cached_result.progress.update(
                        current=progress_data.get("current", 0),
                        total=progress_data.get("total", 0),
                        message=progress_data.get("message", ""),
                        **progress_data.get("details", {}),
                    )

                if "result_data" in celery_result.info:
                    cached_result.result_data = celery_result.info["result_data"]

            # Update completion time if job finished
            if cached_result.is_completed and not cached_result.completed_at:
                cached_result.completed_at = datetime.utcnow()

            self._store_job_result(cached_result)
            return cached_result

        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        celery_result = AsyncResult(job_id, app=self.celery_app)

        if celery_result.state in ["PENDING", "STARTED", "PROGRESS"]:
            celery_result.revoke(terminate=True)

            # Update job status
            job_result = self._get_job_result(job_id)
            if job_result:
                job_result.status = JobStatus.REVOKED
                job_result.completed_at = datetime.utcnow()
                self._store_job_result(job_result)

            # Remove from active jobs
            self.redis_client.srem(self.job_list_key, job_id)

            # Update statistics
            self._update_job_stats("cancelled")

            return True

        return False

    def list_jobs(
        self,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[JobResult]:
        """List jobs with optional filtering."""
        # Get active job IDs
        job_ids = list(self.redis_client.smembers(self.job_list_key))

        jobs = []
        for job_id in job_ids[offset : offset + limit]:
            job_result = self.get_job_status(job_id.decode())
            if job_result:
                # Apply filters
                if job_type and job_result.job_type != job_type:
                    continue
                if status and job_result.status != status:
                    continue

                jobs.append(job_result)

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        return jobs

    def cleanup_completed_jobs(self, older_than_hours: int = 24) -> int:
        """Clean up completed jobs older than specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        job_ids = list(self.redis_client.smembers(self.job_list_key))
        cleaned_count = 0

        for job_id in job_ids:
            job_result = self._get_job_result(job_id.decode())
            if (
                job_result
                and job_result.is_completed
                and job_result.completed_at
                and job_result.completed_at < cutoff_time
            ):
                # Remove from Redis
                self.redis_client.delete(f"{self.job_prefix}{job_id.decode()}")
                self.redis_client.srem(self.job_list_key, job_id)
                cleaned_count += 1

        return cleaned_count

    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        stats_data = self.redis_client.get(self.job_stats_key)
        if stats_data:
            result = json.loads(stats_data)
            return dict(result) if isinstance(result, dict) else {}

        return {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "by_type": {},
            "last_updated": datetime.utcnow().isoformat(),
        }

    def update_job_progress(
        self, job_id: str, current: int, total: int, message: str = "", **details
    ) -> None:
        """Update job progress (called from within tasks)."""
        job_result = self._get_job_result(job_id)
        if job_result:
            job_result.progress.update(current, total, message, **details)
            job_result.status = JobStatus.PROGRESS
            self._store_job_result(job_result)

    def _store_job_result(self, job_result: JobResult) -> None:
        """Store job result in Redis."""
        key = f"{self.job_prefix}{job_result.job_id}"
        data = {
            "job_id": job_result.job_id,
            "status": job_result.status.value,
            "job_type": job_result.job_type.value,
            "created_at": job_result.created_at.isoformat(),
            "started_at": (
                job_result.started_at.isoformat() if job_result.started_at else None
            ),
            "completed_at": (
                job_result.completed_at.isoformat() if job_result.completed_at else None
            ),
            "progress": {
                "current": job_result.progress.current,
                "total": job_result.progress.total,
                "percentage": job_result.progress.percentage,
                "message": job_result.progress.message,
                "details": job_result.progress.details,
            },
            "result_data": job_result.result_data,
            "error_message": job_result.error_message,
            "error_traceback": job_result.error_traceback,
            "retry_count": job_result.retry_count,
            "max_retries": job_result.max_retries,
            "metadata": job_result.metadata,
        }

        self.redis_client.setex(
            key, timedelta(days=7), json.dumps(data, default=str)  # Keep for 7 days
        )

    def _get_job_result(self, job_id: str) -> Optional[JobResult]:
        """Get job result from Redis."""
        key = f"{self.job_prefix}{job_id}"
        data = self.redis_client.get(key)

        if data:
            job_data = json.loads(data)

            progress = JobProgress(
                current=job_data["progress"]["current"],
                total=job_data["progress"]["total"],
                percentage=job_data["progress"]["percentage"],
                message=job_data["progress"]["message"],
                details=job_data["progress"]["details"],
            )

            return JobResult(
                job_id=job_data["job_id"],
                status=JobStatus(job_data["status"]),
                job_type=JobType(job_data["job_type"]),
                created_at=datetime.fromisoformat(job_data["created_at"]),
                started_at=(
                    datetime.fromisoformat(job_data["started_at"])
                    if job_data["started_at"]
                    else None
                ),
                completed_at=(
                    datetime.fromisoformat(job_data["completed_at"])
                    if job_data["completed_at"]
                    else None
                ),
                progress=progress,
                result_data=job_data["result_data"],
                error_message=job_data["error_message"],
                error_traceback=job_data["error_traceback"],
                retry_count=job_data["retry_count"],
                max_retries=job_data["max_retries"],
                metadata=job_data["metadata"],
            )

        return None

    def _update_job_stats(
        self, action: str, job_type: Optional[JobType] = None
    ) -> None:
        """Update job statistics."""
        stats = self.get_job_statistics()

        if action == "submitted":
            stats["total_submitted"] += 1
        elif action == "completed":
            stats["total_completed"] += 1
        elif action == "failed":
            stats["total_failed"] += 1
        elif action == "cancelled":
            stats["total_cancelled"] += 1

        if job_type:
            type_key = job_type.value
            if type_key not in stats["by_type"]:
                stats["by_type"][type_key] = {
                    "submitted": 0,
                    "completed": 0,
                    "failed": 0,
                    "cancelled": 0,
                }

            stats["by_type"][type_key][action] += 1

        stats["last_updated"] = datetime.utcnow().isoformat()

        self.redis_client.setex(
            self.job_stats_key,
            timedelta(days=30),  # Keep stats for 30 days
            json.dumps(stats),
        )


# Global job manager instance
job_manager = JobManager()
