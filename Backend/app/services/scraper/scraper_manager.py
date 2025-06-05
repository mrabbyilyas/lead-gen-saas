"""Manager for handling scraping jobs and orchestrating the scraping process."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from .base_scraper import ScrapingResult, ScrapingStatus, ScrapingConfig
from .scraper_factory import (
    ScraperFactory,
    ScraperType,
    create_scraper,
    auto_select_scraper,
)
from .rate_limiter import RateLimiter
from .proxy_manager import ProxyManager


class ScrapingJob:
    """Represents a scraping job with metadata and results."""

    def __init__(
        self,
        job_id: str,
        query: str,
        scraper_type: Union[ScraperType, str],
        config: Optional[ScrapingConfig] = None,
        metadata: Optional[Dict] = None,
    ):
        self.job_id = job_id
        self.query = query
        self.scraper_type = scraper_type
        self.config = config
        self.metadata = metadata or {}
        self.status = ScrapingStatus.PENDING
        self.result: Optional[ScrapingResult] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.progress: float = 0.0

    def start(self) -> None:
        """Mark job as started."""
        self.status = ScrapingStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: ScrapingResult) -> None:
        """Mark job as completed with result."""
        self.status = result.status
        self.result = result
        self.completed_at = datetime.now()
        self.progress = 100.0

    def fail(self, error_message: str) -> None:
        """Mark job as failed with error message."""
        self.status = ScrapingStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()

    def update_progress(self, progress: float) -> None:
        """Update job progress."""
        self.progress = min(max(progress, 0.0), 100.0)

    def to_dict(self) -> Dict:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "query": self.query,
            "scraper_type": (
                self.scraper_type.value
                if isinstance(self.scraper_type, ScraperType)
                else self.scraper_type
            ),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "result_summary": self._get_result_summary() if self.result else None,
        }

    def _get_result_summary(self) -> Dict:
        """Get summary of scraping result."""
        if not self.result:
            return {}

        return {
            "status": self.result.status.value,
            "execution_time": self.result.execution_time,
            "total_pages_scraped": self.result.total_pages_scraped,
            "total_records_found": self.result.total_records_found,
            "companies_count": len(self.result.companies),
            "contacts_count": len(self.result.contacts),
            "errors": self.result.errors,
            "warnings": self.result.warnings,
        }


class ScraperManager:
    """Manager for handling scraping jobs and orchestrating the scraping process."""

    def __init__(
        self,
        scraper_factory: Optional[ScraperFactory] = None,
        rate_limiter: Optional[RateLimiter] = None,
        proxy_manager: Optional[ProxyManager] = None,
        default_config: Optional[ScrapingConfig] = None,
        max_concurrent_jobs: int = 5,
    ):
        self.logger = logging.getLogger(__name__)
        self.scraper_factory = scraper_factory or ScraperFactory()
        self.rate_limiter = rate_limiter
        self.proxy_manager = proxy_manager
        self.default_config = default_config
        self.max_concurrent_jobs = max_concurrent_jobs

        # Set up rate limiter and proxy manager in factory
        if self.rate_limiter:
            self.scraper_factory.set_rate_limiter(self.rate_limiter)

        if self.proxy_manager:
            self.scraper_factory.set_proxy_manager(self.proxy_manager)

        if self.default_config:
            self.scraper_factory.set_default_config(self.default_config)

        # Job tracking
        self.jobs: Dict[str, ScrapingJob] = {}
        self.active_jobs: Set[str] = set()
        self.job_queue: List[str] = []
        self.job_semaphore = asyncio.Semaphore(max_concurrent_jobs)

    async def create_job(
        self,
        query: str,
        scraper_type: Union[ScraperType, str] = ScraperType.AUTO,
        config: Optional[ScrapingConfig] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Create a new scraping job.

        Args:
            query: Search query or URL
            scraper_type: Type of scraper to use
            config: Optional scraping configuration
            metadata: Optional metadata for the job

        Returns:
            Job ID
        """
        job_id = str(uuid4())

        # Create job
        job = ScrapingJob(
            job_id=job_id,
            query=query,
            scraper_type=scraper_type,
            config=config or self.default_config,
            metadata=metadata,
        )

        # Store job
        self.jobs[job_id] = job
        self.job_queue.append(job_id)

        # Start job processing
        asyncio.create_task(self._process_job_queue())

        self.logger.info(f"Created scraping job {job_id} for query: {query}")
        return job_id

    async def create_batch_job(
        self,
        queries: List[str],
        scraper_type: Union[ScraperType, str] = ScraperType.AUTO,
        config: Optional[ScrapingConfig] = None,
        metadata: Optional[Dict] = None,
    ) -> List[str]:
        """Create multiple scraping jobs for batch processing.

        Args:
            queries: List of search queries or URLs
            scraper_type: Type of scraper to use
            config: Optional scraping configuration
            metadata: Optional metadata for the jobs

        Returns:
            List of job IDs
        """
        job_ids = []

        for query in queries:
            job_id = await self.create_job(
                query=query, scraper_type=scraper_type, config=config, metadata=metadata
            )
            job_ids.append(job_id)

        return job_ids

    async def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job information.

        Args:
            job_id: Job ID

        Returns:
            Job information or None if not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return None

        return job.to_dict()

    async def get_job_result(self, job_id: str) -> Optional[ScrapingResult]:
        """Get job result.

        Args:
            job_id: Job ID

        Returns:
            Scraping result or None if not available
        """
        job = self.jobs.get(job_id)
        if not job or not job.result:
            return None

        return job.result

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            True if job was cancelled, False otherwise
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        # Can only cancel pending jobs
        if job.status == ScrapingStatus.PENDING:
            if job_id in self.job_queue:
                self.job_queue.remove(job_id)

            job.status = ScrapingStatus.CANCELLED
            self.logger.info(f"Cancelled job {job_id}")
            return True

        return False

    async def list_jobs(
        self,
        status: Optional[Union[ScrapingStatus, str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """List jobs with optional filtering.

        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            offset: Offset for pagination

        Returns:
            List of job information
        """
        # Convert string status to enum if needed
        if isinstance(status, str):
            try:
                status = ScrapingStatus(status)
            except ValueError:
                pass

        # Filter and sort jobs
        filtered_jobs = []
        for job in self.jobs.values():
            if status is None or job.status == status:
                filtered_jobs.append(job)

        # Sort by creation time (newest first)
        filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Apply pagination
        paginated_jobs = filtered_jobs[offset : offset + limit]

        # Convert to dictionaries
        return [job.to_dict() for job in paginated_jobs]

    async def get_job_stats(self) -> Dict[str, Any]:
        """Get statistics about jobs.

        Returns:
            Dictionary with job statistics
        """
        stats: Dict[str, Any] = {
            "total_jobs": len(self.jobs),
            "active_jobs": len(self.active_jobs),
            "queued_jobs": len(self.job_queue),
            "status_counts": {},
        }

        # Count jobs by status
        for status in ScrapingStatus:
            stats["status_counts"][status.value] = 0

        for job in self.jobs.values():
            stats["status_counts"][job.status.value] += 1

        return stats

    async def _process_job_queue(self) -> None:
        """Process jobs in the queue."""
        while self.job_queue:
            # Get next job ID
            job_id = self.job_queue[0]

            # Check if job still exists and is pending
            job = self.jobs.get(job_id)
            if not job or job.status != ScrapingStatus.PENDING:
                self.job_queue.pop(0)
                continue

            # Wait for semaphore (limit concurrent jobs)
            async with self.job_semaphore:
                # Remove job from queue
                self.job_queue.pop(0)

                # Process job
                self.active_jobs.add(job_id)
                try:
                    await self._execute_job(job)
                finally:
                    self.active_jobs.remove(job_id)

    async def _execute_job(self, job: ScrapingJob) -> None:
        """Execute a scraping job.

        Args:
            job: Job to execute
        """
        self.logger.info(f"Starting job {job.job_id} for query: {job.query}")
        job.start()

        try:
            # Create scraper
            if job.scraper_type == ScraperType.AUTO:
                scraper = auto_select_scraper(job.query, job.config)
            else:
                scraper = create_scraper(job.scraper_type, job.config)

            # Set up progress callback
            scraper.set_progress_callback(lambda p: job.update_progress(p))

            # Execute scraping
            result = await scraper.scrape(job.query, **job.metadata)

            # Store result
            job.complete(result)

            self.logger.info(
                f"Completed job {job.job_id} with status {result.status.value}. "
                f"Found {result.total_records_found} records."
            )

        except Exception as e:
            self.logger.exception(f"Error executing job {job.job_id}: {e}")
            job.fail(str(e))

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs.

        Args:
            max_age_hours: Maximum age of jobs to keep in hours

        Returns:
            Number of jobs cleaned up
        """
        now = datetime.now()
        jobs_to_remove = []

        for job_id, job in self.jobs.items():
            # Only clean up completed, failed, or cancelled jobs
            if job.status not in [
                ScrapingStatus.COMPLETED,
                ScrapingStatus.FAILED,
                ScrapingStatus.CANCELLED,
                ScrapingStatus.BLOCKED,
                ScrapingStatus.RATE_LIMITED,
            ]:
                continue

            # Check if job is old enough
            if job.completed_at:
                age_hours = (now - job.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)

        # Remove old jobs
        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        self.logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        return len(jobs_to_remove)


# Global manager instance
scraper_manager = ScraperManager()


# Convenience functions
async def create_scraping_job(
    query: str,
    scraper_type: Union[ScraperType, str] = ScraperType.AUTO,
    config: Optional[ScrapingConfig] = None,
    metadata: Optional[Dict] = None,
) -> str:
    """Convenience function to create a scraping job."""
    return await scraper_manager.create_job(query, scraper_type, config, metadata)


async def get_scraping_result(job_id: str) -> Optional[ScrapingResult]:
    """Convenience function to get a scraping result."""
    return await scraper_manager.get_job_result(job_id)
