"""Background tasks for analytics operations."""

import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.core.celery_app import celery_app
from app.services.data_processing.business_intelligence import (
    BusinessIntelligenceEngine,
)
from app.services.supabase_service import SupabaseService
from .job_status import JobStatus, JobType
from .job_manager import job_manager


@celery_app.task(bind=True, name="generate_analytics_report_task")
def generate_analytics_report_task(
    self,
    company_ids: List[str],
    report_type: str = "comprehensive",
    report_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate analytics report for companies in background."""
    job_id = self.request.id
    report_config = report_config or {}

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        # Initialize services
        bi_engine = BusinessIntelligenceEngine()
        supabase_service = SupabaseService(table_name="companies")

        total_companies = len(company_ids)
        analyzed_companies = []
        failed_companies = []

        for i, company_id in enumerate(company_ids):
            try:
                # Update progress
                job_manager.update_job_progress(
                    job_id,
                    current=i,
                    total=total_companies,
                    message=f"Analyzing company {company_id}",
                    current_company_id=company_id,
                )

                # Get company data
                company_data = supabase_service.get_company_by_id(company_id)  # type: ignore
                if not company_data:
                    failed_companies.append(
                        {
                            "company_id": company_id,
                            "error": "Company not found",
                            "status": "failed",
                        }
                    )
                    continue

                # Perform business intelligence analysis
                analysis_result = bi_engine.analyze_company(company_data)

                # Store analysis results
                supabase_service.store_company_analysis(  # type: ignore
                    company_id, analysis_result
                )

                analyzed_companies.append(
                    {
                        "company_id": company_id,
                        "name": company_data.get("name"),
                        "growth_score": analysis_result.growth_score,  # type: ignore
                        "opportunity_score": analysis_result.opportunity_score,
                        "risk_score": analysis_result.risk_score,
                        "confidence": analysis_result.confidence,
                        "growth_signals_count": len(analysis_result.growth_signals),
                        "pain_points_count": len(analysis_result.pain_points),
                        "status": "success",
                    }
                )

            except Exception as e:
                failed_companies.append(
                    {"company_id": company_id, "error": str(e), "status": "failed"}
                )

        # Generate summary analytics
        if analyzed_companies:
            avg_growth_score = sum(c["growth_score"] for c in analyzed_companies) / len(
                analyzed_companies
            )
            avg_opportunity_score = sum(
                c["opportunity_score"] for c in analyzed_companies
            ) / len(analyzed_companies)
            avg_risk_score = sum(c["risk_score"] for c in analyzed_companies) / len(
                analyzed_companies
            )
            avg_confidence = sum(c["confidence"] for c in analyzed_companies) / len(
                analyzed_companies
            )

            high_growth_companies = len(
                [c for c in analyzed_companies if c["growth_score"] >= 80]
            )
            high_opportunity_companies = len(
                [c for c in analyzed_companies if c["opportunity_score"] >= 80]
            )
            low_risk_companies = len(
                [c for c in analyzed_companies if c["risk_score"] <= 30]
            )
        else:
            avg_growth_score = avg_opportunity_score = avg_risk_score = (
                avg_confidence
            ) = 0
            high_growth_companies = high_opportunity_companies = low_risk_companies = 0

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=total_companies,
            total=total_companies,
            message="Analytics report generation completed",
            analyzed_count=len(analyzed_companies),
            failed_count=len(failed_companies),
        )

        # Prepare report data
        report_data = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "analyzed_companies": analyzed_companies,
            "failed_companies": failed_companies,
            "summary": {
                "total_companies": total_companies,
                "successfully_analyzed": len(analyzed_companies),
                "failed_analysis": len(failed_companies),
                "average_scores": {
                    "growth": avg_growth_score,
                    "opportunity": avg_opportunity_score,
                    "risk": avg_risk_score,
                    "confidence": avg_confidence,
                },
                "insights": {
                    "high_growth_companies": high_growth_companies,
                    "high_opportunity_companies": high_opportunity_companies,
                    "low_risk_companies": low_risk_companies,
                },
            },
        }

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = report_data
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.ANALYTICS)

        return {"status": "success", "report": report_data}

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
        job_manager._update_job_stats("failed", JobType.ANALYTICS)

        raise


@celery_app.task(bind=True, name="update_job_statistics")
def update_job_statistics(self) -> Dict[str, Any]:
    """Update job execution statistics (periodic task)."""
    job_id = self.request.id

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        # Get current statistics
        current_stats = job_manager.get_job_statistics()

        # Get active jobs count
        active_jobs = job_manager.list_jobs(limit=1000)

        # Calculate additional metrics
        running_jobs = len([j for j in active_jobs if j.is_running])
        completed_jobs = len([j for j in active_jobs if j.is_completed])

        # Calculate average completion times by job type
        completion_times = {}
        for job_type in JobType:
            type_jobs = [
                j
                for j in active_jobs
                if j.job_type == job_type and j.duration is not None
            ]
            if type_jobs:
                avg_duration = sum(
                    j.duration for j in type_jobs if j.duration is not None
                ) / len(type_jobs)
                completion_times[job_type.value] = {
                    "average_duration_seconds": avg_duration,
                    "sample_size": len(type_jobs),
                }

        # Update statistics with additional metrics
        enhanced_stats = {
            **current_stats,
            "current_metrics": {
                "active_jobs": len(active_jobs),
                "running_jobs": running_jobs,
                "completed_jobs": completed_jobs,
                "completion_times": completion_times,
                "last_calculated": datetime.utcnow().isoformat(),
            },
        }

        # Store enhanced statistics
        job_manager.redis_client.setex(
            f"{job_manager.job_stats_key}:enhanced",
            timedelta(hours=1),
            str(enhanced_stats),
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = enhanced_stats
            job_manager._store_job_result(job_result)

        return {"status": "success", "statistics": enhanced_stats}

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


@celery_app.task(bind=True, name="batch_business_intelligence_analysis")
def batch_business_intelligence_analysis(
    self, company_ids: List[str], analysis_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Perform batch business intelligence analysis in background."""
    job_id = self.request.id
    analysis_config = analysis_config or {}

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

        # Initialize services
        bi_engine = BusinessIntelligenceEngine()
        supabase_service = SupabaseService(table_name="companies")

        total_companies = len(company_ids)
        analyzed_companies = []
        failed_companies = []

        # Batch process companies
        for i in range(0, total_companies, 10):  # Process in batches of 10
            batch = company_ids[i : i + 10]

            # Update progress
            job_manager.update_job_progress(
                job_id,
                current=i,
                total=total_companies,
                message=f"Processing batch {i//10 + 1}/{(total_companies + 9)//10}",
                batch_size=len(batch),
            )

            # Get batch company data
            batch_companies = supabase_service.get_companies_by_ids(batch)  # type: ignore

            # Analyze batch
            batch_results = bi_engine.batch_analyze_companies(  # type: ignore
                batch_companies, **analysis_config
            )  # type: ignore

            # Process results
            for company_id, result in batch_results.items():
                if result.get("status") == "success":
                    analysis = result["analysis"]

                    # Store analysis
                    supabase_service.store_company_analysis(  # type: ignore
                        company_id, analysis
                    )

                    analyzed_companies.append(
                        {
                            "company_id": company_id,
                            "analysis": analysis.to_dict(),
                            "status": "success",
                        }
                    )
                else:
                    failed_companies.append(
                        {
                            "company_id": company_id,
                            "error": result.get("error", "Unknown error"),
                            "status": "failed",
                        }
                    )

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=total_companies,
            total=total_companies,
            message="Batch analysis completed",
            analyzed_count=len(analyzed_companies),
            failed_count=len(failed_companies),
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "analyzed_companies": analyzed_companies,
                "failed_companies": failed_companies,
                "total_processed": total_companies,
                "success_count": len(analyzed_companies),
                "failure_count": len(failed_companies),
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.ANALYTICS)

        return {
            "status": "success",
            "analyzed_companies": analyzed_companies,
            "failed_companies": failed_companies,
            "summary": {
                "total": total_companies,
                "success": len(analyzed_companies),
                "failed": len(failed_companies),
            },
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
        job_manager._update_job_stats("failed", JobType.ANALYTICS)

        raise
