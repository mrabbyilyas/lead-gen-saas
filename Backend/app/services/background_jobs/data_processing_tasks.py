"""Background tasks for data processing operations."""

import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.celery_app import celery_app
from app.services.data_processing.pipeline import DataProcessingPipeline
from app.services.data_processing.lead_scoring import LeadScoringEngine
from app.services.data_processing.enrichment import DataEnrichmentService  # type: ignore
from app.services.supabase_service import SupabaseService
from app.services.websocket_service import get_websocket_service
from .job_status import JobStatus, JobType
from .job_manager import job_manager


@celery_app.task(bind=True, name="process_scraped_data_task")
def process_scraped_data_task(
    self, company_ids: List[str], processing_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process scraped company data in background."""
    job_id = self.request.id
    processing_config = processing_config or {}

    try:
        # Initialize variables
        total_companies = len(company_ids)
        processed_companies: List[Dict[str, Any]] = []
        failed_companies: List[Dict[str, Any]] = []

        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

            # Send WebSocket notification for job start
            websocket_service = get_websocket_service()
            websocket_service.notify_job_progress(
                job_id=job_id,
                status=JobStatus.STARTED,
                progress_percentage=0.0,
                processed_targets=0,
                total_targets=total_companies,
                message="Starting data processing job",
            )

        # Initialize services
        pipeline = DataProcessingPipeline()
        supabase_service = SupabaseService(table_name="companies")

        for i, company_id in enumerate(company_ids):
            try:
                # Update progress
                job_manager.update_job_progress(
                    job_id,
                    current=i,
                    total=total_companies,
                    message=f"Processing company {company_id}",
                    current_company_id=company_id,
                )

                # Send WebSocket progress notification
                websocket_service = get_websocket_service()
                progress_percentage = (i / total_companies) * 100
                websocket_service.notify_job_progress(
                    job_id=job_id,
                    status=JobStatus.PROGRESS,
                    progress_percentage=progress_percentage,
                    processed_targets=i,
                    total_targets=total_companies,
                    companies_found=len(processed_companies),
                    message=f"Processing company {company_id}",
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

                # Process the data
                processed_data = pipeline.process_company_data(  # type: ignore
                    company_data, **processing_config
                )

                # Update company with processed data
                updated_company = supabase_service.update_company_data(  # type: ignore
                    company_id, processed_data
                )

                processed_companies.append(
                    {
                        "company_id": company_id,
                        "name": company_data.get("name"),
                        "processed_fields": list(processed_data.keys()),
                        "status": "success",
                    }
                )

            except Exception as e:
                failed_companies.append(
                    {"company_id": company_id, "error": str(e), "status": "failed"}
                )

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=total_companies,
            total=total_companies,
            message="Data processing completed",
            processed_count=len(processed_companies),
            failed_count=len(failed_companies),
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "processed_companies": processed_companies,
                "failed_companies": failed_companies,
                "total_processed": total_companies,
                "success_count": len(processed_companies),
                "failure_count": len(failed_companies),
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.DATA_PROCESSING)

        return {
            "status": "success",
            "processed_companies": processed_companies,
            "failed_companies": failed_companies,
            "summary": {
                "total": total_companies,
                "success": len(processed_companies),
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
        job_manager._update_job_stats("failed", JobType.DATA_PROCESSING)

        raise


@celery_app.task(bind=True, name="calculate_lead_scores_task")
def calculate_lead_scores_task(
    self, company_ids: List[str], scoring_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate lead scores for companies in background."""
    job_id = self.request.id
    scoring_config = scoring_config or {}

    try:
        # Initialize variables
        total_companies = len(company_ids)
        scored_companies: List[Dict[str, Any]] = []
        failed_companies: List[Dict[str, Any]] = []

        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

            # Send WebSocket notification for job start
            websocket_service = get_websocket_service()
            websocket_service.notify_job_progress(
                job_id=job_id,
                status=JobStatus.STARTED,
                progress_percentage=0.0,
                processed_targets=0,
                total_targets=total_companies,
                message="Starting data processing job",
            )

        # Initialize services
        scoring_engine = LeadScoringEngine()
        supabase_service = SupabaseService(table_name="companies")

        for i, company_id in enumerate(company_ids):
            try:
                # Update progress
                job_manager.update_job_progress(
                    job_id,
                    current=i,
                    total=total_companies,
                    message=f"Calculating lead score for company {company_id}",
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

                # Calculate lead score
                lead_score = scoring_engine.calculate_lead_score(  # type: ignore
                    company_data, **scoring_config
                )

                # Update company with lead score
                supabase_service.update_company_lead_score(  # type: ignore
                    company_id, lead_score
                )

                scored_companies.append(
                    {
                        "company_id": company_id,
                        "name": company_data.get("name"),
                        "lead_score": lead_score.score,
                        "score_breakdown": lead_score.breakdown,
                        "status": "success",
                    }
                )

            except Exception as e:
                failed_companies.append(
                    {"company_id": company_id, "error": str(e), "status": "failed"}
                )

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=total_companies,
            total=total_companies,
            message="Lead scoring completed",
            scored_count=len(scored_companies),
            failed_count=len(failed_companies),
        )

        # Calculate summary statistics
        scores = [c["lead_score"] for c in scored_companies]
        avg_score = sum(scores) / len(scores) if scores else 0
        high_quality_leads = len([s for s in scores if s >= 80])

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "scored_companies": scored_companies,
                "failed_companies": failed_companies,
                "total_processed": total_companies,
                "success_count": len(scored_companies),
                "failure_count": len(failed_companies),
                "average_score": avg_score,
                "high_quality_leads": high_quality_leads,
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.LEAD_SCORING)

        return {
            "status": "success",
            "scored_companies": scored_companies,
            "failed_companies": failed_companies,
            "summary": {
                "total": total_companies,
                "success": len(scored_companies),
                "failed": len(failed_companies),
                "average_score": avg_score,
                "high_quality_leads": high_quality_leads,
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
        job_manager._update_job_stats("failed", JobType.LEAD_SCORING)

        raise


@celery_app.task(bind=True, name="enrich_company_data_task")
async def enrich_company_data_task(
    self, company_ids: List[str], enrichment_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Enrich company data with additional information in background."""
    job_id = self.request.id
    enrichment_config = enrichment_config or {}

    try:
        # Initialize variables
        total_companies = len(company_ids)
        enriched_companies: List[Dict[str, Any]] = []
        failed_companies: List[Dict[str, Any]] = []

        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

            # Send WebSocket notification for job start
            websocket_service = get_websocket_service()
            websocket_service.notify_job_progress(
                job_id=job_id,
                status=JobStatus.STARTED,
                progress_percentage=0.0,
                processed_targets=0,
                total_targets=total_companies,
                message="Starting data processing job",
            )

        # Initialize services
        enrichment_service = DataEnrichmentService()
        supabase_service = SupabaseService(table_name="companies")

        for i, company_id in enumerate(company_ids):
            try:
                # Update progress
                job_manager.update_job_progress(
                    job_id,
                    current=i,
                    total=total_companies,
                    message=f"Enriching company {company_id}",
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

                # Enrich the data
                enriched_data = await enrichment_service.enrich_company_data(  # type: ignore
                    company_data
                )

                # Update company with enriched data
                updated_company = supabase_service.update_company_data(  # type: ignore
                    company_id, enriched_data
                )

                enriched_companies.append(
                    {
                        "company_id": company_id,
                        "name": company_data.get("name"),
                        "enriched_fields": list(enriched_data.enriched_data.keys()),
                        "status": "success",
                    }
                )

            except Exception as e:
                failed_companies.append(
                    {"company_id": company_id, "error": str(e), "status": "failed"}
                )

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=total_companies,
            total=total_companies,
            message="Data enrichment completed",
            enriched_count=len(enriched_companies),
            failed_count=len(failed_companies),
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "enriched_companies": enriched_companies,
                "failed_companies": failed_companies,
                "total_processed": total_companies,
                "success_count": len(enriched_companies),
                "failure_count": len(failed_companies),
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.DATA_PROCESSING)

        return {
            "status": "success",
            "enriched_companies": enriched_companies,
            "failed_companies": failed_companies,
            "summary": {
                "total": total_companies,
                "success": len(enriched_companies),
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
        job_manager._update_job_stats("failed", JobType.DATA_PROCESSING)

        raise
