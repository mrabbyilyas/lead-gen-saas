"""API endpoints for background job management."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.background_jobs import (
    JobStatus,
    JobType,
    JobPriority,
    job_manager,
)

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


# Request Models
class ScrapeCompaniesRequest(BaseModel):
    """Request model for scraping multiple companies."""

    company_urls: List[str] = Field(..., description="List of company URLs to scrape")
    scrape_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Scraping configuration"
    )
    priority: Optional[str] = Field(
        default="normal", description="Job priority (low, normal, high, critical)"
    )


class ScrapeCompanyRequest(BaseModel):
    """Request model for scraping a single company."""

    company_url: str = Field(..., description="Company URL to scrape")
    scrape_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Scraping configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


class BatchScrapeRequest(BaseModel):
    """Request model for batch scraping."""

    search_queries: List[str] = Field(
        ..., description="Search queries for finding companies"
    )
    max_results_per_query: int = Field(
        default=10, description="Maximum results per query"
    )
    scrape_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Scraping configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


class ProcessDataRequest(BaseModel):
    """Request model for processing company data."""

    company_ids: List[str] = Field(..., description="List of company IDs to process")
    processing_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Processing configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


class CalculateScoresRequest(BaseModel):
    """Request model for calculating lead scores."""

    company_ids: List[str] = Field(..., description="List of company IDs to score")
    scoring_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Scoring configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


class EnrichDataRequest(BaseModel):
    """Request model for enriching company data."""

    company_ids: List[str] = Field(..., description="List of company IDs to enrich")
    enrichment_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Enrichment configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


class GenerateReportRequest(BaseModel):
    """Request model for generating analytics reports."""

    company_ids: List[str] = Field(..., description="List of company IDs to analyze")
    report_type: str = Field(
        default="comprehensive", description="Type of report to generate"
    )
    report_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Report configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


class AnalyzeCompaniesRequest(BaseModel):
    """Request model for business intelligence analysis."""

    company_ids: List[str] = Field(..., description="List of company IDs to analyze")
    analysis_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Analysis configuration"
    )
    priority: Optional[str] = Field(default="normal", description="Job priority")


# Response Models
class JobResponse(BaseModel):
    """Response model for job operations."""

    job_id: str
    status: str
    job_type: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str
    status: str
    job_type: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: Dict[str, Any]
    result_data: Dict[str, Any]
    error_message: Optional[str]
    duration: Optional[float]
    metadata: Dict[str, Any]


def _get_priority(priority_str: Optional[str]) -> JobPriority:
    """Convert priority string to JobPriority enum, with fallback to NORMAL."""
    if priority_str is None:
        return JobPriority.NORMAL

    priority_map = {
        "low": JobPriority.LOW,
        "normal": JobPriority.NORMAL,
        "high": JobPriority.HIGH,
        "critical": JobPriority.CRITICAL,
    }
    return priority_map.get(priority_str.lower(), JobPriority.NORMAL)


# Scraping Endpoints
@router.post("/scrape/companies", response_model=JobResponse)
async def scrape_companies(request: ScrapeCompaniesRequest):
    """Submit a job to scrape multiple companies."""
    try:
        job_id = job_manager.submit_job(
            task_name="scrape_companies_task",
            job_type=JobType.SCRAPING,
            args=(request.company_urls, request.scrape_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_count": len(request.company_urls),
                "scrape_config": request.scrape_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="scraping",
            message=f"Scraping job submitted for {len(request.company_urls)} companies",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/company", response_model=JobResponse)
async def scrape_company(request: ScrapeCompanyRequest):
    """Submit a job to scrape a single company."""
    try:
        job_id = job_manager.submit_job(
            task_name="scrape_single_company_task",
            job_type=JobType.SCRAPING,
            args=(request.company_url, request.scrape_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_url": request.company_url,
                "scrape_config": request.scrape_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="scraping",
            message=f"Scraping job submitted for {request.company_url}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/batch", response_model=JobResponse)
async def batch_scrape(request: BatchScrapeRequest):
    """Submit a batch scraping job based on search queries."""
    try:
        job_id = job_manager.submit_job(
            task_name="batch_scrape_task",
            job_type=JobType.SCRAPING,
            args=(
                request.search_queries,
                request.max_results_per_query,
                request.scrape_config,
            ),
            priority=_get_priority(request.priority),
            metadata={
                "query_count": len(request.search_queries),
                "max_results_per_query": request.max_results_per_query,
                "scrape_config": request.scrape_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="scraping",
            message=f"Batch scraping job submitted for {len(request.search_queries)} queries",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data Processing Endpoints
@router.post("/process/data", response_model=JobResponse)
async def process_data(request: ProcessDataRequest):
    """Submit a job to process company data."""
    try:
        job_id = job_manager.submit_job(
            task_name="process_scraped_data_task",
            job_type=JobType.DATA_PROCESSING,
            args=(request.company_ids, request.processing_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_count": len(request.company_ids),
                "processing_config": request.processing_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="data_processing",
            message=f"Data processing job submitted for {len(request.company_ids)} companies",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/scores", response_model=JobResponse)
async def calculate_scores(request: CalculateScoresRequest):
    """Submit a job to calculate lead scores."""
    try:
        job_id = job_manager.submit_job(
            task_name="calculate_lead_scores_task",
            job_type=JobType.LEAD_SCORING,
            args=(request.company_ids, request.scoring_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_count": len(request.company_ids),
                "scoring_config": request.scoring_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="lead_scoring",
            message=f"Lead scoring job submitted for {len(request.company_ids)} companies",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/enrich", response_model=JobResponse)
async def enrich_data(request: EnrichDataRequest):
    """Submit a job to enrich company data."""
    try:
        job_id = job_manager.submit_job(
            task_name="enrich_company_data_task",
            job_type=JobType.DATA_PROCESSING,
            args=(request.company_ids, request.enrichment_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_count": len(request.company_ids),
                "enrichment_config": request.enrichment_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="data_processing",
            message=f"Data enrichment job submitted for {len(request.company_ids)} companies",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints
@router.post("/analytics/report", response_model=JobResponse)
async def generate_report(request: GenerateReportRequest):
    """Submit a job to generate analytics report."""
    try:
        job_id = job_manager.submit_job(
            task_name="generate_analytics_report_task",
            job_type=JobType.ANALYTICS,
            args=(request.company_ids, request.report_type, request.report_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_count": len(request.company_ids),
                "report_type": request.report_type,
                "report_config": request.report_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="analytics",
            message=f"Analytics report job submitted for {len(request.company_ids)} companies",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/analyze", response_model=JobResponse)
async def analyze_companies(request: AnalyzeCompaniesRequest):
    """Submit a job for business intelligence analysis."""
    try:
        job_id = job_manager.submit_job(
            task_name="batch_business_intelligence_analysis",
            job_type=JobType.ANALYTICS,
            args=(request.company_ids, request.analysis_config),
            priority=_get_priority(request.priority),
            metadata={
                "company_count": len(request.company_ids),
                "analysis_config": request.analysis_config,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="analytics",
            message=f"Business intelligence analysis job submitted for {len(request.company_ids)} companies",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Maintenance Endpoints
@router.post("/maintenance/cleanup", response_model=JobResponse)
async def cleanup_old_data(
    older_than_days: int = Query(
        default=90, description="Delete data older than this many days"
    )
):
    """Submit a job to clean up old company data."""
    try:
        job_id = job_manager.submit_job(
            task_name="cleanup_old_company_data",
            job_type=JobType.MAINTENANCE,
            args=(older_than_days,),
            priority=JobPriority.LOW,
            metadata={
                "older_than_days": older_than_days,
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="maintenance",
            message=f"Data cleanup job submitted for data older than {older_than_days} days",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/health-check", response_model=JobResponse)
async def health_check():
    """Submit a system health check job."""
    try:
        job_id = job_manager.submit_job(
            task_name="system_health_check",
            job_type=JobType.MAINTENANCE,
            priority=JobPriority.HIGH,
            metadata={
                "check_type": "system_health",
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="maintenance",
            message="System health check job submitted",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/optimize-db", response_model=JobResponse)
async def optimize_db():
    """Submit a database optimization job."""
    try:
        job_id = job_manager.submit_job(
            task_name="optimize_database",
            job_type=JobType.MAINTENANCE,
            priority=JobPriority.LOW,
            metadata={
                "optimization_type": "database",
            },
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            job_type="maintenance",
            message="Database optimization job submitted",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Job Management Endpoints
@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    try:
        job_result = job_manager.get_job_status(job_id)
        if not job_result:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobStatusResponse(
            job_id=job_result.job_id,
            status=job_result.status.value,
            job_type=job_result.job_type.value,
            created_at=job_result.created_at,
            started_at=job_result.started_at,
            completed_at=job_result.completed_at,
            progress={
                "current": job_result.progress.current,
                "total": job_result.progress.total,
                "percentage": job_result.progress.percentage,
                "message": job_result.progress.message,
                "details": job_result.progress.details,
            },
            result_data=job_result.result_data,
            error_message=job_result.error_message,
            duration=job_result.duration,
            metadata=job_result.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_jobs(
    job_type: Optional[str] = Query(default=None, description="Filter by job type"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, description="Maximum number of jobs to return"),
    offset: int = Query(default=0, description="Number of jobs to skip"),
):
    """List jobs with optional filtering."""
    try:
        # Convert string filters to enums
        job_type_filter = None
        if job_type:
            try:
                job_type_filter = JobType(job_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid job type: {job_type}"
                )

        status_filter = None
        if status:
            try:
                status_filter = JobStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        jobs = job_manager.list_jobs(
            job_type=job_type_filter,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        return {
            "jobs": [job.to_dict() for job in jobs],
            "total": len(jobs),
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    try:
        success = job_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (not running or already completed)",
            )

        return {"message": f"Job {job_id} has been cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_job_statistics():
    """Get job execution statistics."""
    try:
        stats = job_manager.get_job_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
