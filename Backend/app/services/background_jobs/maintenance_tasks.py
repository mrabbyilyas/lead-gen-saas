"""Background tasks for system maintenance operations."""

import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.core.celery_app import celery_app
from app.services.supabase_service import SupabaseService
from .job_status import JobStatus, JobType
from .job_manager import job_manager


@celery_app.task(bind=True, name="cleanup_expired_jobs")
def cleanup_expired_jobs(
    self, max_age_hours: int = 24, cleanup_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Clean up expired jobs from Redis (periodic task)."""
    job_id = self.request.id

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        # Perform cleanup
        cleaned_count = job_manager.cleanup_completed_jobs(max_age_hours)

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "cleaned_jobs_count": cleaned_count,
                "older_than_hours": max_age_hours,
                "cleanup_time": datetime.utcnow().isoformat(),
            }
            job_manager._store_job_result(job_result)

        return {
            "status": "success",
            "cleaned_jobs_count": cleaned_count,
            "older_than_hours": max_age_hours,
        }

    except Exception as e:
        # Update job status to failed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.FAILURE
            job_result.completed_at = datetime.utcnow()
            job_result.error_message = str(e)
            job_result.error_traceback = traceback.format_exc()
            job_manager._store_job_result(job_result)

        raise


@celery_app.task(bind=True, name="cleanup_old_company_data")
def cleanup_old_company_data(
    self, max_age_days: int = 90, cleanup_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Clean up old company data from database."""
    job_id = self.request.id

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        # Initialize service
        supabase_service = SupabaseService(table_name="companies")

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        # Clean up old data
        cleanup_result = supabase_service.cleanup_old_data(cutoff_date)  # type: ignore

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "cleanup_result": cleanup_result,
                "older_than_days": max_age_days,
                "cutoff_date": cutoff_date.isoformat(),
                "cleanup_time": datetime.utcnow().isoformat(),
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.MAINTENANCE)

        return {
            "status": "success",
            "cleanup_result": cleanup_result,
            "older_than_days": max_age_days,
        }

    except Exception as e:
        # Update job status to failed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.FAILURE
            job_result.completed_at = datetime.utcnow()
            job_result.error_message = str(e)
            job_result.error_traceback = traceback.format_exc()
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("failed", JobType.MAINTENANCE)

        raise


@celery_app.task(bind=True, name="system_health_check")
def system_health_check(
    self, check_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Perform system health check."""
    job_id = self.request.id

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        health_status: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "overall_status": "healthy",
        }

        # Check Redis connection
        try:
            job_manager.redis_client.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "response_time_ms": "< 1",
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        # Check Supabase connection
        try:
            supabase_service = SupabaseService(table_name="companies")
            test_result = supabase_service.health_check()  # type: ignore
            health_status["services"]["supabase"] = {
                "status": "healthy" if test_result else "unhealthy",
                "response_time_ms": "< 100",
            }
            if not test_result:
                health_status["overall_status"] = "degraded"
        except Exception as e:
            health_status["services"]["supabase"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        # Check Celery worker status
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            worker_count = len(active_workers) if active_workers else 0

            health_status["services"]["celery_workers"] = {
                "status": "healthy" if worker_count > 0 else "unhealthy",
                "active_workers": worker_count,
                "workers": list(active_workers.keys()) if active_workers else [],
            }

            if worker_count == 0:
                health_status["overall_status"] = "critical"

        except Exception as e:
            health_status["services"]["celery_workers"] = {
                "status": "unknown",
                "error": str(e),
            }

        # Get job statistics
        try:
            job_stats = job_manager.get_job_statistics()
            health_status["job_statistics"] = job_stats
        except Exception as e:
            health_status["job_statistics"] = {"error": str(e)}

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = health_status
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.MAINTENANCE)

        return {"status": "success", "health_check": health_status}

    except Exception as e:
        # Update job status to failed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.FAILURE
            job_result.completed_at = datetime.utcnow()
            job_result.error_message = str(e)
            job_result.error_traceback = traceback.format_exc()
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("failed", JobType.MAINTENANCE)

        raise


@celery_app.task(bind=True, name="optimize_database")
def optimize_database(
    self, optimization_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Optimize database performance."""
    job_id = self.request.id

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        # Initialize service
        supabase_service = SupabaseService(table_name="companies")

        optimization_results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "operations": [],
        }

        # Update progress
        job_manager.update_job_progress(
            job_id, current=1, total=4, message="Analyzing database statistics"
        )

        # Analyze database statistics
        try:
            stats_result = supabase_service.analyze_database_statistics()  # type: ignore
            optimization_results["operations"].append(
                {
                    "operation": "analyze_statistics",
                    "status": "success",
                    "result": stats_result,
                }
            )
        except Exception as e:
            optimization_results["operations"].append(
                {"operation": "analyze_statistics", "status": "failed", "error": str(e)}
            )

        # Update progress
        job_manager.update_job_progress(
            job_id, current=2, total=4, message="Updating table statistics"
        )

        # Update table statistics
        try:
            update_result = supabase_service.update_table_statistics()  # type: ignore
            optimization_results["operations"].append(
                {
                    "operation": "update_table_statistics",
                    "status": "success",
                    "result": update_result,
                }
            )
        except Exception as e:
            optimization_results["operations"].append(
                {
                    "operation": "update_table_statistics",
                    "status": "failed",
                    "error": str(e),
                }
            )

        # Update progress
        job_manager.update_job_progress(
            job_id, current=3, total=4, message="Cleaning up temporary data"
        )

        # Clean up temporary data
        try:
            cleanup_result = supabase_service.cleanup_temporary_data()  # type: ignore
            optimization_results["operations"].append(
                {
                    "operation": "cleanup_temporary_data",
                    "status": "success",
                    "result": cleanup_result,
                }
            )
        except Exception as e:
            optimization_results["operations"].append(
                {
                    "operation": "cleanup_temporary_data",
                    "status": "failed",
                    "error": str(e),
                }
            )

        # Final progress update
        job_manager.update_job_progress(
            job_id, current=4, total=4, message="Database optimization completed"
        )

        # Calculate success rate
        successful_ops = len(
            [
                op
                for op in optimization_results["operations"]
                if op["status"] == "success"
            ]
        )
        total_ops = len(optimization_results["operations"])
        success_rate = (successful_ops / total_ops * 100) if total_ops > 0 else 0

        optimization_results["summary"] = {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "success_rate_percent": success_rate,
        }

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = optimization_results
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.MAINTENANCE)

        return {"status": "success", "optimization_results": optimization_results}

    except Exception as e:
        # Update job status to failed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.FAILURE
            job_result.completed_at = datetime.utcnow()
            job_result.error_message = str(e)
            job_result.error_traceback = traceback.format_exc()
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("failed", JobType.MAINTENANCE)

        raise
