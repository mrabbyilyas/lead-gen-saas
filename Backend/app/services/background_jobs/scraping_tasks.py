"""Background tasks for web scraping operations."""

import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.celery_app import celery_app
from app.services.scraper.scraper_manager import ScraperManager
from app.services.supabase_service import SupabaseService
from app.services.websocket_service import get_websocket_service
from .job_status import JobStatus, JobType
from .job_manager import job_manager


@celery_app.task(bind=True, name="scrape_companies_task")
def scrape_companies_task(
    self, company_urls: List[str], scrape_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Scrape multiple companies in background."""
    job_id = self.request.id
    scrape_config = scrape_config or {}

    try:
        # Update job status to started
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.STARTED
            job_result.started_at = datetime.utcnow()
            job_manager._store_job_result(job_result)

            # Initialize variables
        total_companies = len(company_urls)
        scraped_companies: List[Dict[str, Any]] = []
        failed_companies: List[Dict[str, Any]] = []

        # Send initial WebSocket notification
        websocket_service = get_websocket_service()
        websocket_service.notify_job_progress(
            job_id=job_id,
            status=JobStatus.STARTED,
            progress_percentage=0.0,
            processed_targets=0,
            total_targets=total_companies,
            message="Starting company scraping job",
        )

        # Initialize scraper manager
        scraper_manager = ScraperManager()
        supabase_service = SupabaseService(table_name="companies")

        for i, company_url in enumerate(company_urls):
            try:
                # Update progress
                job_manager.update_job_progress(
                    job_id,
                    current=i,
                    total=total_companies,
                    message=f"Scraping {company_url}",
                    current_url=company_url,
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
                    companies_found=len(scraped_companies),
                    message=f"Scraping {company_url}",
                )

                # Scrape company
                company_data = scraper_manager.scrape_company(  # type: ignore
                    url=company_url, **scrape_config
                )

                if company_data:
                    # Store in database
                    stored_company = supabase_service.store_company_data(company_data)  # type: ignore  # type: ignore
                    scraped_companies.append(
                        {
                            "url": company_url,
                            "company_id": stored_company.get("id"),
                            "name": company_data.get("name"),
                            "status": "success",
                        }
                    )
                else:
                    failed_companies.append(
                        {
                            "url": company_url,
                            "error": "No data scraped",
                            "status": "failed",
                        }
                    )

            except Exception as e:
                failed_companies.append(
                    {"url": company_url, "error": str(e), "status": "failed"}
                )

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=total_companies,
            total=total_companies,
            message="Scraping completed",
            scraped_count=len(scraped_companies),
            failed_count=len(failed_companies),
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "scraped_companies": scraped_companies,
                "failed_companies": failed_companies,
                "total_processed": total_companies,
                "success_count": len(scraped_companies),
                "failure_count": len(failed_companies),
            }
            job_manager._store_job_result(job_result)

            # Send WebSocket completion notification
            websocket_service = get_websocket_service()
            websocket_service.notify_job_completion(
                job_id=job_id,
                status=JobStatus.SUCCESS,
                total_companies=len(scraped_companies),
                total_contacts=0,
                job_type="company_scraping",
                summary=f"Successfully scraped {len(scraped_companies)} companies, {len(failed_companies)} failed",
                result_data={
                    "scraped_companies": len(scraped_companies),
                    "failed_companies": len(failed_companies),
                    "total_processed": total_companies,
                },
            )

        # Update statistics
        job_manager._update_job_stats("completed", JobType.SCRAPING)

        return {
            "status": "success",
            "scraped_companies": scraped_companies,
            "failed_companies": failed_companies,
            "summary": {
                "total": total_companies,
                "success": len(scraped_companies),
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

            # Send WebSocket error notification
            websocket_service = get_websocket_service()
            websocket_service.notify_job_error(
                job_id=job_id,
                error_message=str(e),
                error_details={
                    "error_type": "ScrapeError",
                    "traceback_info": traceback.format_exc(),
                },
            )

        # Update statistics
        job_manager._update_job_stats("failed", JobType.SCRAPING)

        raise


@celery_app.task(bind=True, name="scrape_single_company_task")
def scrape_single_company_task(
    self, company_url: str, scrape_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Scrape a single company in background."""
    job_id = self.request.id
    scrape_config = scrape_config or {}

    try:
        # Initialize variables
        total_companies = 1  # Single company task

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
                message="Starting company scraping job",
            )

        # Initialize scraper manager
        scraper_manager = ScraperManager()
        supabase_service = SupabaseService(table_name="companies")

        # Update progress
        job_manager.update_job_progress(
            job_id,
            current=0,
            total=1,
            message=f"Scraping {company_url}",
            url=company_url,
        )

        # Scrape company
        company_data = scraper_manager.scrape_company(  # type: ignore
            url=company_url, **scrape_config
        )

        if not company_data:
            raise ValueError("No data could be scraped from the provided URL")

        # Store in database
        stored_company = supabase_service.store_company_data(company_data)  # type: ignore

        # Final progress update
        job_manager.update_job_progress(
            job_id,
            current=1,
            total=1,
            message="Scraping completed",
            company_name=company_data.get("name"),
            company_id=stored_company.get("id"),
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "company_data": company_data,
                "company_id": stored_company.get("id"),
                "url": company_url,
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.SCRAPING)

        return {
            "status": "success",
            "company_data": company_data,
            "company_id": stored_company.get("id"),
            "url": company_url,
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

            # Send WebSocket error notification
            websocket_service = get_websocket_service()
            websocket_service.notify_job_error(
                job_id=job_id,
                error_message=str(e),
                error_details={
                    "error_type": "ScrapeError",
                    "traceback_info": traceback.format_exc(),
                },
            )

        # Update statistics
        job_manager._update_job_stats("failed", JobType.SCRAPING)

        raise


@celery_app.task(bind=True, name="batch_scrape_task")
def batch_scrape_task(
    self,
    search_queries: List[str],
    max_results_per_query: int = 10,
    scrape_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Perform batch scraping based on search queries."""
    job_id = self.request.id
    scrape_config = scrape_config or {}

    try:
        # Initialize variables
        total_companies = 1  # Single company task

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
                message="Starting company scraping job",
            )

        # Initialize scraper manager
        scraper_manager = ScraperManager()
        supabase_service = SupabaseService(table_name="companies")

        total_queries = len(search_queries)
        all_results = []
        query_results = {}

        for i, query in enumerate(search_queries):
            try:
                # Update progress
                job_manager.update_job_progress(
                    job_id,
                    current=i,
                    total=total_queries,
                    message=f"Processing query: {query}",
                    current_query=query,
                )

                # Search for companies
                search_results = scraper_manager.search_companies(  # type: ignore
                    query=query, max_results=max_results_per_query, **scrape_config
                )

                query_companies = []

                # Scrape each found company
                for j, company_url in enumerate(search_results):
                    try:
                        # Update sub-progress
                        job_manager.update_job_progress(
                            job_id,
                            current=i,
                            total=total_queries,
                            message=f"Scraping company {j+1}/{len(search_results)} for query: {query}",
                            current_query=query,
                            current_url=company_url,
                            sub_progress=f"{j+1}/{len(search_results)}",
                        )

                        company_data = scraper_manager.scrape_company(  # type: ignore
                            url=company_url, **scrape_config
                        )

                        if company_data:
                            # Store in database
                            stored_company = supabase_service.store_company_data(company_data)  # type: ignore
                            company_result = {
                                "url": company_url,
                                "company_id": stored_company.get("id"),
                                "name": company_data.get("name"),
                                "data": company_data,
                                "status": "success",
                            }
                            query_companies.append(company_result)
                            all_results.append(company_result)

                    except Exception as e:
                        query_companies.append(
                            {"url": company_url, "error": str(e), "status": "failed"}
                        )

                query_results[query] = {
                    "companies": query_companies,
                    "total_found": len(search_results),
                    "successfully_scraped": len(
                        [c for c in query_companies if c["status"] == "success"]
                    ),
                    "failed": len(
                        [c for c in query_companies if c["status"] == "failed"]
                    ),
                }

            except Exception as e:
                query_results[query] = {"error": str(e), "status": "failed"}

        # Final progress update
        total_scraped = len([r for r in all_results if r["status"] == "success"])
        total_failed = len([r for r in all_results if r["status"] == "failed"])

        job_manager.update_job_progress(
            job_id,
            current=total_queries,
            total=total_queries,
            message="Batch scraping completed",
            total_companies_scraped=total_scraped,
            total_companies_failed=total_failed,
        )

        # Update job status to completed
        job_result = job_manager._get_job_result(job_id)
        if job_result:
            job_result.status = JobStatus.SUCCESS
            job_result.completed_at = datetime.utcnow()
            job_result.result_data = {
                "query_results": query_results,
                "summary": {
                    "total_queries": total_queries,
                    "total_companies_found": len(all_results),
                    "total_companies_scraped": total_scraped,
                    "total_companies_failed": total_failed,
                },
            }
            job_manager._store_job_result(job_result)

        # Update statistics
        job_manager._update_job_stats("completed", JobType.SCRAPING)

        return {
            "status": "success",
            "query_results": query_results,
            "summary": {
                "total_queries": total_queries,
                "total_companies_found": len(all_results),
                "total_companies_scraped": total_scraped,
                "total_companies_failed": total_failed,
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

            # Send WebSocket error notification
            websocket_service = get_websocket_service()
            websocket_service.notify_job_error(
                job_id=job_id,
                error_message=str(e),
                error_details={
                    "error_type": "ScrapeError",
                    "traceback_info": traceback.format_exc(),
                },
            )

        # Update statistics
        job_manager._update_job_stats("failed", JobType.SCRAPING)

        raise
