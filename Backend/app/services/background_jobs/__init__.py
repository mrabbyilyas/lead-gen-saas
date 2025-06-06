"""Background job processing module."""

from .job_manager import JobManager

# Create a global job manager instance
job_manager = JobManager()
from .job_status import JobStatus, JobType, JobPriority
from .scraping_tasks import (
    scrape_companies_task,
    scrape_single_company_task,
    batch_scrape_task,
)
from .data_processing_tasks import (
    process_scraped_data_task,
    calculate_lead_scores_task,
    enrich_company_data_task,
)
from .analytics_tasks import (
    generate_analytics_report_task,
    update_job_statistics,
)

__all__ = [
    "JobManager",
    "job_manager",
    "JobStatus",
    "JobType",
    "JobPriority",
    "scrape_companies_task",
    "scrape_single_company_task",
    "batch_scrape_task",
    "process_scraped_data_task",
    "calculate_lead_scores_task",
    "enrich_company_data_task",
    "generate_analytics_report_task",
    "update_job_statistics",
]
