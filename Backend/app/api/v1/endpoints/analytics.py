from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Union
import logging

from app.core.database import get_supabase_client
from app.models.schemas import (
    AnalyticsTimeRange,
    JobSummaryAnalytics,
    AnalyticsResponse,
    LeadQualityDistribution,
    ContactDataInsights,
    IndustryBreakdown,
    TechnologyTrends,
)
from app.models.api_schemas import AnalyticsRequest
from app.services.data_processing.business_intelligence import (
    analyze_company_intelligence,
    batch_analyze_companies,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    """Get dashboard analytics data with business intelligence insights"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Get basic metrics from database
        supabase = get_supabase_client()

        # Get total leads
        total_leads_result = (
            supabase.table("companies").select("id", count="exact").execute()
        )
        total_leads = total_leads_result.count or 0

        # Get new leads today
        today = datetime.utcnow().date().isoformat()
        new_leads_result = (
            supabase.table("companies")
            .select("id", count="exact")
            .gte("created_at", today)
            .execute()
        )
        new_leads_today = new_leads_result.count or 0

        # Get top industries
        industries_result = (
            supabase.table("companies")
            .select("industry")
            .not_.is_("industry", "null")
            .execute()
        )
        industry_counts: Dict[str, int] = {}
        for row in industries_result.data:
            industry = row.get("industry")
            if industry:
                industry_counts[industry] = industry_counts.get(industry, 0) + 1

        top_industries = [
            {"industry": k, "count": v}
            for k, v in sorted(
                industry_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Calculate conversion rate (simplified)
        qualified_leads_result = (
            supabase.table("companies")
            .select("id", count="exact")
            .gte("lead_score", 70)
            .execute()
        )
        qualified_leads = qualified_leads_result.count or 0
        conversion_rate = (qualified_leads / max(total_leads, 1)) * 100

        return {
            "total_leads": total_leads,
            "new_leads_today": new_leads_today,
            "conversion_rate": round(conversion_rate, 2),
            "top_industries": top_industries,
            "lead_sources": ["LinkedIn", "Google", "Company Websites"],
            "date_range": {"start": start_date, "end": end_date},
            "business_intelligence": {
                "growth_signals_detected": new_leads_today * 2,  # Estimated
                "pain_points_identified": total_leads // 10,  # Estimated
                "competitive_insights": len(top_industries),
            },
        }

    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve dashboard analytics"
        )


@router.get("/trends")
async def get_lead_trends(
    period: str = Query("7d", regex="^(7d|30d|90d)$"),
    metric: str = Query("count", regex="^(count|conversion|score|growth_signals)$"),
):
    """Get lead trends over time with business intelligence metrics"""
    try:
        # Parse period
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map[period]

        start_date = datetime.utcnow() - timedelta(days=days)

        if metric == "count":
            # Get lead count trends
            supabase = get_supabase_client()
            companies_result = (
                supabase.table("companies")
                .select("created_at")
                .gte("created_at", start_date.isoformat())
                .execute()
            )

            # Group by date
            date_counts: Dict[str, int] = {}
            for row in companies_result.data:
                created_at = datetime.fromisoformat(
                    row["created_at"].replace("Z", "+00:00")
                )
                date_key = created_at.date().isoformat()
                date_counts[date_key] = date_counts.get(date_key, 0) + 1

            data_points = [
                {"date": date, "value": count}
                for date, count in sorted(date_counts.items())
            ]

        elif metric == "growth_signals":
            # Simulate growth signals trend (would be real data in production)
            growth_data_points: List[Dict[str, Any]] = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                # Simulate growth signal detection
                value = max(0, int((i % 7) * 2 + (i // 7)))
                growth_data_points.append(
                    {"date": date.strftime("%Y-%m-%d"), "value": value}
                )
            data_points = growth_data_points

        else:
            # Default to count for other metrics
            data_points = []

        # Calculate summary
        valid_points: List[float] = []
        for point in data_points:
            point_value: Any = point.get("value")
            if isinstance(point_value, (int, float)):
                valid_points.append(float(point_value))
        total = sum(valid_points)
        average = total / len(data_points) if data_points else 0

        # Calculate growth rate
        if len(data_points) >= 2:
            first_half = data_points[: len(data_points) // 2]
            second_half = data_points[len(data_points) // 2 :]

            first_valid: List[float] = []
            for p in first_half:
                p_value: Any = p.get("value")
                if isinstance(p_value, (int, float)):
                    first_valid.append(float(p_value))

            second_valid: List[float] = []
            for p in second_half:
                p_value2: Any = p.get("value")
                if isinstance(p_value2, (int, float)):
                    second_valid.append(float(p_value2))

            first_avg = sum(first_valid) / len(first_half) if first_half else 0
            second_avg = sum(second_valid) / len(second_half) if second_half else 0
            growth_rate = ((second_avg - first_avg) / max(first_avg, 1)) * 100
        else:
            growth_rate = 0.0

        return {
            "period": period,
            "metric": metric,
            "data_points": data_points,
            "summary": {
                "total": total,
                "average": round(average, 2),
                "growth_rate": round(growth_rate, 2),
            },
        }

    except Exception as e:
        logger.error(f"Error getting lead trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lead trends")


@router.get("/performance")
async def get_scraping_performance():
    """Get scraping performance metrics with business intelligence insights"""
    try:
        # Get scraping job metrics
        supabase = get_supabase_client()

        # Get all scraping jobs
        total_jobs_result = supabase.table("scraping_jobs").select("*").execute()
        total_scrapes = len(total_jobs_result.data)

        # Get successful jobs
        successful_jobs_result = (
            supabase.table("scraping_jobs")
            .select("*")
            .eq("status", "completed")
            .execute()
        )
        successful_scrapes = len(successful_jobs_result.data)

        # Get failed jobs
        failed_jobs_result = (
            supabase.table("scraping_jobs").select("*").eq("status", "failed").execute()
        )
        failed_scrapes = len(failed_jobs_result.data)

        # Calculate success rate
        success_rate = (successful_scrapes / max(total_scrapes, 1)) * 100

        # Calculate average duration for completed jobs
        if successful_jobs_result.data:
            durations = []
            for job in successful_jobs_result.data:
                if job.get("created_at") and job.get("updated_at"):
                    created = datetime.fromisoformat(
                        job["created_at"].replace("Z", "+00:00")
                    )
                    updated = datetime.fromisoformat(
                        job["updated_at"].replace("Z", "+00:00")
                    )
                    durations.append((updated - created).total_seconds())
            average_duration = sum(durations) / len(durations) if durations else 0.0
        else:
            average_duration = 0.0

        # Get last 24h metrics
        yesterday = datetime.utcnow() - timedelta(hours=24)
        last_24h_jobs_result = (
            supabase.table("scraping_jobs")
            .select("id", count="exact")
            .gte("created_at", yesterday.isoformat())
            .execute()
        )
        last_24h_scrapes = last_24h_jobs_result.count or 0

        last_24h_leads_result = (
            supabase.table("companies")
            .select("id", count="exact")
            .gte("created_at", yesterday.isoformat())
            .execute()
        )
        last_24h_leads = last_24h_leads_result.count or 0

        return {
            "total_scrapes": total_scrapes,
            "successful_scrapes": successful_scrapes,
            "failed_scrapes": failed_scrapes,
            "average_duration": round(average_duration, 2),
            "success_rate": round(success_rate, 2),
            "last_24h": {"scrapes": last_24h_scrapes, "leads_found": last_24h_leads},
            "business_intelligence": {
                "data_quality_score": min(success_rate, 100.0),
                "processing_efficiency": max(
                    0, 100 - (average_duration / 60)
                ),  # Efficiency based on duration
                "lead_generation_rate": round(
                    (last_24h_leads / max(last_24h_scrapes, 1)), 2
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting scraping performance: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve scraping performance"
        )


@router.get("/export-stats")
async def get_export_stats():
    """Get export statistics"""
    try:
        supabase = get_supabase_client()

        # Get export statistics
        total_exports_result = (
            supabase.table("exports").select("id", count="exact").execute()
        )
        total_exports = total_exports_result.count or 0

        successful_exports_result = (
            supabase.table("exports")
            .select("id", count="exact")
            .eq("status", "completed")
            .execute()
        )
        successful_exports = successful_exports_result.count or 0

        failed_exports_result = (
            supabase.table("exports")
            .select("id", count="exact")
            .eq("status", "failed")
            .execute()
        )
        failed_exports = failed_exports_result.count or 0

        # Calculate success rate
        success_rate = (
            (successful_exports / total_exports * 100) if total_exports > 0 else 0.0
        )

        # Get exports today
        today = datetime.utcnow().date().isoformat()
        exports_today_result = (
            supabase.table("exports")
            .select("id", count="exact")
            .gte("created_at", today)
            .execute()
        )
        exports_today = exports_today_result.count or 0

        return {
            "total_exports": total_exports,
            "successful_exports": successful_exports,
            "failed_exports": failed_exports,
            "success_rate": round(success_rate, 2),
            "exports_today": exports_today,
            "popular_formats": ["CSV", "JSON", "Excel"],
            "average_export_size": 150,  # Average number of records
        }

    except Exception as e:
        logger.error(f"Error getting export stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve export statistics"
        )


@router.get("/summary")
async def get_analytics_summary(
    job_id: Optional[str] = Query(None, description="Filter by specific job ID")
) -> AnalyticsResponse:
    """Get comprehensive analytics summary with business intelligence insights"""
    try:
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        time_range = AnalyticsTimeRange(start_date=start_date, end_date=end_date)

        # Get job summary analytics
        supabase = get_supabase_client()

        if job_id:
            # Filter by specific job
            leads_result = (
                supabase.table("companies")
                .select("id", count="exact")
                .eq("scraping_job_id", job_id)
                .execute()
            )
            total_leads = leads_result.count or 0

            job_result = (
                supabase.table("scraping_jobs")
                .select("created_at", "updated_at", "status")
                .eq("id", job_id)
                .execute()
            )

            if job_result.data:
                job = job_result.data[0]
                created = datetime.fromisoformat(
                    job["created_at"].replace("Z", "+00:00")
                )
                updated = (
                    datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
                    if job.get("updated_at")
                    else created
                )
                processing_time = (updated - created).total_seconds()
                success_rate = 100.0 if job["status"] == "completed" else 0.0
            else:
                processing_time = 0.0
                success_rate = 0.0
        else:
            # Get overall metrics
            total_leads_result = (
                supabase.table("companies").select("id", count="exact").execute()
            )
            total_leads = total_leads_result.count or 0

            # Get completed jobs for processing time calculation
            completed_jobs_result = (
                supabase.table("scraping_jobs")
                .select("created_at", "updated_at")
                .eq("status", "completed")
                .execute()
            )

            if completed_jobs_result.data:
                durations = []
                for job in completed_jobs_result.data:
                    if job.get("created_at") and job.get("updated_at"):
                        created = datetime.fromisoformat(
                            job["created_at"].replace("Z", "+00:00")
                        )
                        updated = datetime.fromisoformat(
                            job["updated_at"].replace("Z", "+00:00")
                        )
                        durations.append((updated - created).total_seconds())
                processing_time = sum(durations) / len(durations) if durations else 0.0
            else:
                processing_time = 0.0

            # Get success rate
            all_jobs_result = supabase.table("scraping_jobs").select("status").execute()
            if all_jobs_result.data:
                completed_count = len(
                    [
                        job
                        for job in all_jobs_result.data
                        if job["status"] == "completed"
                    ]
                )
                total_count = len(all_jobs_result.data)
                success_rate = (
                    (completed_count / total_count) * 100 if total_count > 0 else 0.0
                )
            else:
                success_rate = 0.0

        # Get job statistics
        all_jobs_result = supabase.table("scraping_jobs").select("status").execute()
        total_jobs = len(all_jobs_result.data) if all_jobs_result.data else 0
        completed_jobs = (
            len(
                [
                    job
                    for job in all_jobs_result.data
                    if job.get("status") == "completed"
                ]
            )
            if all_jobs_result.data
            else 0
        )
        failed_jobs = (
            len([job for job in all_jobs_result.data if job.get("status") == "failed"])
            if all_jobs_result.data
            else 0
        )
        running_jobs = (
            len([job for job in all_jobs_result.data if job.get("status") == "running"])
            if all_jobs_result.data
            else 0
        )

        # Get total counts
        total_companies_result = (
            supabase.table("companies").select("id", count="exact").execute()
        )
        total_companies = total_companies_result.count or 0

        total_contacts_result = (
            supabase.table("contacts").select("id", count="exact").execute()
        )
        total_contacts = total_contacts_result.count or 0

        job_summary = JobSummaryAnalytics(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            running_jobs=running_jobs,
            total_companies_found=total_companies,
            total_contacts_found=total_contacts,
            average_completion_time=120.5,  # Example value
            success_rate=Decimal(str(completed_jobs / max(total_jobs, 1))),
        )

        # Get lead quality distribution
        quality_result = (
            supabase.table("companies")
            .select("lead_score")
            .not_.is_("lead_score", "null")
            .execute()
        )

        hot_count = len(
            [c for c in quality_result.data if c.get("lead_score", 0) >= 80]
        )
        warm_count = len(
            [c for c in quality_result.data if 60 <= c.get("lead_score", 0) < 80]
        )
        cold_count = len(
            [c for c in quality_result.data if c.get("lead_score", 0) < 60]
        )

        quality_result = [
            ("hot", hot_count),
            ("warm", warm_count),
            ("cold", cold_count),
        ]

        total_scored = sum(row[1] for row in quality_result)

        # Create simple counts for schema
        hot_leads = next(
            (count for quality, count in quality_result if quality == "hot"), 0
        )
        warm_leads = next(
            (count for quality, count in quality_result if quality == "warm"), 0
        )
        cold_leads = next(
            (count for quality, count in quality_result if quality == "cold"), 0
        )

        # Calculate average score from the original quality_result
        if quality_result:
            scores = [
                c.get("lead_score", 0)
                for c in quality_result
                if isinstance(c, dict) and c.get("lead_score") is not None
            ]
            average_score = sum(scores) / len(scores) if scores else 0.0
        else:
            average_score = 0.0

        lead_quality_distribution = {
            "high": hot_leads,
            "medium": warm_leads,
            "low": cold_leads,
            "average_score": average_score,
        }

        # Get contact analytics
        contacts_result = (
            supabase.table("contacts")
            .select("email", "phone", "seniority_level")
            .execute()
        )

        total_contacts = len(contacts_result.data)
        verified_emails = len([c for c in contacts_result.data if c.get("email")])
        verified_phones = len([c for c in contacts_result.data if c.get("phone")])
        decision_makers = len(
            [
                c
                for c in contacts_result.data
                if c.get("seniority_level") in ["C-Level", "VP", "Director"]
            ]
        )

        contact_result = (
            total_contacts,
            verified_emails,
            verified_phones,
            decision_makers,
        )

        contact_analytics = {
            "total_contacts": contact_result[0],
            "verified_emails": contact_result[1],
            "verified_phones": contact_result[2],
            "decision_makers": contact_result[3],
            "email_verification_rate": round(
                contact_result[1] / max(contact_result[0], 1) * 100, 1
            ),
            "phone_verification_rate": round(
                contact_result[2] / max(contact_result[0], 1) * 100, 1
            ),
        }

        # Get industry breakdown
        industries_result = (
            supabase.table("companies")
            .select("industry")
            .not_.is_("industry", "null")
            .execute()
        )
        industry_counts: Dict[str, int] = {}
        for row in industries_result.data:
            industry = row.get("industry")
            if industry:
                industry_counts[industry] = industry_counts.get(industry, 0) + 1

        industry_breakdown = [
            {"industry": k, "count": v}
            for k, v in sorted(
                industry_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Get company size distribution
        sizes_result = (
            supabase.table("companies")
            .select("company_size")
            .not_.is_("company_size", "null")
            .execute()
        )
        size_counts: Dict[str, int] = {}
        for row in sizes_result.data:
            size = row.get("company_size")
            if size:
                size_counts[size] = size_counts.get(size, 0) + 1

        company_size_distribution = [
            {"size": k, "count": v}
            for k, v in sorted(size_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Get technology trends
        tech_result = (
            supabase.table("companies")
            .select("technologies")
            .not_.is_("technologies", "null")
            .execute()
        )
        tech_counts: Dict[str, int] = {}
        for row in tech_result.data:
            technologies = row.get("technologies") or []
            if isinstance(technologies, list):
                for tech in technologies:
                    if tech:
                        tech_counts[tech] = tech_counts.get(tech, 0) + 1

        sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
        technology_trends = {
            "most_common": [
                {"technology": k, "count": v} for k, v in sorted_techs[:10]
            ],
            "emerging": [{"technology": k, "count": v} for k, v in sorted_techs[10:15]],
        }

        # Helper function for safe integer conversion
        def safe_int(value: Any, default: int = 0) -> int:
            try:
                if isinstance(value, int):
                    return value
                elif isinstance(value, str) and value.isdigit():
                    return int(value)
                elif isinstance(value, (float, Decimal)):
                    return int(value)
                else:
                    return default
            except (ValueError, TypeError):
                return default

        # Generate engagement opportunities
        engagement_opportunities = [
            {"priority": "high", "type": "growth_signal", "count": total_leads // 3},
            {"priority": "medium", "type": "pain_point", "count": total_leads // 5},
            {
                "priority": "low",
                "type": "technology_upgrade",
                "count": total_leads // 10,
            },
        ]

        return AnalyticsResponse(
            time_range=AnalyticsTimeRange(
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow(),
            ),
            job_summary=job_summary,
            lead_quality=LeadQualityDistribution(
                high_quality=int(lead_quality_distribution.get("high", 0)),
                medium_quality=int(lead_quality_distribution.get("medium", 0)),
                low_quality=int(lead_quality_distribution.get("low", 0)),
                average_score=Decimal(
                    str(lead_quality_distribution.get("average_score", 0.0))
                ),
            ),
            contact_insights=ContactDataInsights(
                total_contacts=int(contact_analytics["total_contacts"]),
                verified_contacts=int(contact_analytics["verified_emails"]),
                decision_makers=int(contact_analytics["decision_makers"]),
                contacts_with_email=int(contact_analytics["verified_emails"]),
                contacts_with_phone=int(contact_analytics["verified_phones"]),
                contacts_with_linkedin=int(contact_analytics["verified_phones"])
                // 2,  # Estimate
                average_experience_years=5.5,
                top_job_titles=[
                    {
                        "title": "CEO",
                        "count": int(contact_analytics["decision_makers"]) // 3,
                    },
                    {
                        "title": "CTO",
                        "count": int(contact_analytics["decision_makers"]) // 4,
                    },
                    {
                        "title": "VP Engineering",
                        "count": int(contact_analytics["decision_makers"]) // 5,
                    },
                ],
                seniority_distribution={
                    "C-Level": int(contact_analytics["decision_makers"]) // 2,
                    "VP": int(contact_analytics["decision_makers"]) // 3,
                    "Director": int(contact_analytics["decision_makers"]) // 4,
                    "Manager": int(contact_analytics["total_contacts"]) // 3,
                },
            ),
            industry_breakdown=IndustryBreakdown(
                industry_distribution={
                    str(item.get("industry", "Unknown")): safe_int(item.get("count", 0))
                    for item in industry_breakdown
                },
                top_industries=[
                    {
                        "industry": str(item.get("industry", "Unknown")),
                        "count": safe_int(item.get("count", 0)),
                    }
                    for item in industry_breakdown[:5]
                ],
                company_size_distribution={
                    str(item.get("size", "Unknown")): safe_int(item.get("count", 0))
                    for item in company_size_distribution
                },
                revenue_distribution={
                    "<$1M": total_leads // 3,
                    "$1M-$10M": total_leads // 2,
                    "$10M+": total_leads // 6,
                },
            ),
            technology_trends=TechnologyTrends(
                top_technologies=[
                    {
                        "technology": str(tech["technology"]),
                        "count": (
                            int(tech["count"])
                            if isinstance(tech["count"], (int, str))
                            else 0
                        ),
                    }
                    for tech in technology_trends["most_common"]
                ],
                technology_adoption_rate={
                    str(tech["technology"]): Decimal(
                        str(float(tech["count"]) / max(total_leads, 1))
                    )
                    for tech in technology_trends["most_common"][:5]
                    if isinstance(tech["count"], (int, float, str))
                },
                emerging_technologies=[
                    str(tech["technology"]) for tech in technology_trends["emerging"]
                ],
                technology_combinations=[
                    {"combination": "React + Node.js", "count": total_leads // 10},
                    {"combination": "Python + Django", "count": total_leads // 15},
                ],
            ),
        )

    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analytics summary"
        )


@router.post("/business-intelligence")
async def analyze_business_intelligence(
    company_ids: List[str] = Query(..., description="List of company IDs to analyze")
):
    """Perform business intelligence analysis on specified companies"""
    try:
        if len(company_ids) > 100:
            raise HTTPException(
                status_code=400, detail="Maximum 100 companies can be analyzed at once"
            )

        # Get company data
        supabase = get_supabase_client()

        companies_result = (
            supabase.table("companies")
            .select(
                "id",
                "name",
                "description",
                "industry",
                "company_size",
                "website",
                "technologies",
                "employee_count",
                "lead_score",
            )
            .in_("id", company_ids)
            .execute()
        )

        companies_data = []
        for company in companies_result.data:
            company_data = {
                "id": company["id"],
                "name": company["name"],
                "description": company.get("description") or "",
                "industry": company.get("industry") or "",
                "company_size": company.get("company_size") or "",
                "website": company.get("website") or "",
                "technologies": company.get("technologies") or [],
                "employee_count": company.get("employee_count"),
                "lead_score": company.get("lead_score"),
            }
            companies_data.append(company_data)

        if not companies_data:
            raise HTTPException(
                status_code=404, detail="No companies found with provided IDs"
            )

        # Perform business intelligence analysis
        if len(companies_data) == 1:
            result = analyze_company_intelligence(companies_data[0])
            return {
                "analysis_type": "single_company",
                "company_id": companies_data[0]["id"],
                "result": result,
            }
        else:
            results = batch_analyze_companies(companies_data)
            return {
                "analysis_type": "batch_analysis",
                "companies_analyzed": len(companies_data),
                "results": results,
                "summary": {
                    "avg_growth_score": sum(r.overall_growth_score for r in results)
                    / len(results),
                    "avg_opportunity_score": sum(r.opportunity_score for r in results)
                    / len(results),
                    "avg_risk_score": sum(r.risk_score for r in results) / len(results),
                    "total_growth_signals": sum(len(r.growth_signals) for r in results),
                    "total_pain_points": sum(len(r.pain_points) for r in results),
                    "total_competitors": sum(len(r.competitors) for r in results),
                },
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in business intelligence analysis: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to perform business intelligence analysis"
        )


@router.get("/growth-signals")
async def get_growth_signals(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
):
    """Get detected growth signals with filtering options"""
    try:
        supabase = get_supabase_client()

        # Get companies for analysis
        if company_id:
            companies_result = (
                supabase.table("companies")
                .select(
                    "id",
                    "name",
                    "description",
                    "industry",
                    "technologies",
                    "employee_count",
                )
                .eq("id", company_id)
                .execute()
            )
        else:
            companies_result = (
                supabase.table("companies")
                .select(
                    "id",
                    "name",
                    "description",
                    "industry",
                    "technologies",
                    "employee_count",
                )
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

        all_signals = []

        for company in companies_result.data:
            company_data = {
                "id": company["id"],
                "name": company["name"],
                "description": company.get("description") or "",
                "industry": company.get("industry") or "",
                "technologies": company.get("technologies") or [],
                "employee_count": company.get("employee_count"),
            }

            # Analyze for growth signals
            from app.services.data_processing.business_intelligence import (
                GrowthSignalDetector,
            )

            signals = GrowthSignalDetector.detect_growth_signals(company_data)

            # Filter by signal type if specified
            if signal_type:
                signals = [s for s in signals if s.signal_type.value == signal_type]

            # Add company info to signals
            for signal in signals:
                signal_dict = {
                    "company_id": company[0],
                    "company_name": company[1],
                    "signal_type": signal.signal_type.value,
                    "description": signal.description,
                    "confidence": signal.confidence,
                    "impact_score": signal.impact_score,
                    "source": signal.source,
                    "detected_at": signal.detected_at.isoformat(),
                    "evidence": signal.evidence,
                }
                all_signals.append(signal_dict)

        # Sort by confidence and impact
        all_signals.sort(
            key=lambda x: (x["confidence"] * x["impact_score"]), reverse=True
        )

        return {
            "total_signals": len(all_signals),
            "signals": all_signals[:limit],
            "signal_types": list(set(s["signal_type"] for s in all_signals)),
            "avg_confidence": (
                sum(s["confidence"] for s in all_signals) / len(all_signals)
                if all_signals
                else 0
            ),
        }

    except Exception as e:
        logger.error(f"Error getting growth signals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve growth signals")


@router.get("/pain-points")
async def get_pain_points(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    category: Optional[str] = Query(None, description="Filter by pain point category"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
):
    """Get identified pain points with filtering options"""
    try:
        supabase = get_supabase_client()

        # Get companies for analysis
        if company_id:
            companies_result = (
                supabase.table("companies")
                .select(
                    "id",
                    "name",
                    "description",
                    "industry",
                    "technologies",
                    "employee_count",
                )
                .eq("id", company_id)
                .execute()
            )
        else:
            companies_result = (
                supabase.table("companies")
                .select(
                    "id",
                    "name",
                    "description",
                    "industry",
                    "technologies",
                    "employee_count",
                )
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

        all_pain_points = []

        for company in companies_result.data:
            company_data = {
                "id": company["id"],
                "name": company["name"],
                "description": company.get("description") or "",
                "industry": company.get("industry") or "",
                "technologies": company.get("technologies") or [],
                "employee_count": company.get("employee_count"),
            }

            # Analyze for pain points
            from app.services.data_processing.business_intelligence import (
                PainPointDetector,
            )

            pain_points = PainPointDetector.detect_pain_points(company_data)

            # Filter by category if specified
            if category:
                pain_points = [
                    pp for pp in pain_points if pp.category.value == category
                ]

            # Add company info to pain points
            for pain_point in pain_points:
                pain_point_dict = {
                    "company_id": company[0],
                    "company_name": company[1],
                    "category": pain_point.category.value,
                    "description": pain_point.description,
                    "confidence": pain_point.confidence,
                    "severity": pain_point.severity,
                    "urgency": pain_point.urgency,
                    "source": pain_point.source,
                    "detected_at": pain_point.detected_at.isoformat(),
                    "keywords": pain_point.keywords,
                    "potential_solutions": pain_point.potential_solutions,
                }
                all_pain_points.append(pain_point_dict)

        # Sort by severity and urgency
        all_pain_points.sort(key=lambda x: (x["severity"] * x["urgency"]), reverse=True)

        return {
            "total_pain_points": len(all_pain_points),
            "pain_points": all_pain_points[:limit],
            "categories": list(set(pp["category"] for pp in all_pain_points)),
            "avg_severity": (
                sum(pp["severity"] for pp in all_pain_points) / len(all_pain_points)
                if all_pain_points
                else 0
            ),
        }

    except Exception as e:
        logger.error(f"Error getting pain points: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pain points")


@router.post("/comprehensive")
async def get_comprehensive_analytics(request: AnalyticsRequest) -> AnalyticsResponse:
    """Get comprehensive analytics with all metrics based on request parameters"""
    try:
        supabase = get_supabase_client()

        # Create time range
        time_range = AnalyticsTimeRange(
            start_date=request.start_date, end_date=request.end_date
        )

        # Initialize response components
        job_summary = JobSummaryAnalytics(success_rate=Decimal(0))
        lead_quality = LeadQualityDistribution(average_score=Decimal(0))
        contact_insights = ContactDataInsights()
        industry_breakdown = IndustryBreakdown()
        technology_trends = TechnologyTrends()

        # Apply filters if provided
        query_filters = {}
        if request.filters:
            for key, value in request.filters.items():
                if key in ["industry", "company_size", "revenue_range"]:
                    query_filters[key] = value

        # Get job summary analytics if requested
        if "job_summary" in request.metrics:
            jobs_query = supabase.table("scraping_jobs").select("*")
            jobs_query = jobs_query.gte("created_at", request.start_date.isoformat())
            jobs_query = jobs_query.lte("created_at", request.end_date.isoformat())
            jobs_result = jobs_query.execute()

            total_jobs = len(jobs_result.data)
            completed_jobs = len(
                [j for j in jobs_result.data if j["status"] == "completed"]
            )
            failed_jobs = len([j for j in jobs_result.data if j["status"] == "failed"])
            running_jobs = len(
                [j for j in jobs_result.data if j["status"] == "running"]
            )

            # Get companies and contacts found
            companies_result = (
                supabase.table("companies")
                .select("id", count="exact")
                .gte("created_at", request.start_date.isoformat())
                .lte("created_at", request.end_date.isoformat())
                .execute()
            )
            contacts_result = (
                supabase.table("contacts")
                .select("id", count="exact")
                .gte("created_at", request.start_date.isoformat())
                .lte("created_at", request.end_date.isoformat())
                .execute()
            )

            # Calculate average completion time
            completed_jobs_data = [
                j
                for j in jobs_result.data
                if j["status"] == "completed" and j.get("updated_at")
            ]
            avg_completion_time = None
            if completed_jobs_data:
                durations = []
                for job in completed_jobs_data:
                    created = datetime.fromisoformat(
                        job["created_at"].replace("Z", "+00:00")
                    )
                    updated = datetime.fromisoformat(
                        job["updated_at"].replace("Z", "+00:00")
                    )
                    durations.append((updated - created).total_seconds())
                avg_completion_time = sum(durations) / len(durations)

            job_summary = JobSummaryAnalytics(
                total_jobs=total_jobs,
                completed_jobs=completed_jobs,
                failed_jobs=failed_jobs,
                running_jobs=running_jobs,
                total_companies_found=companies_result.count or 0,
                total_contacts_found=contacts_result.count or 0,
                average_completion_time=avg_completion_time,
                success_rate=Decimal(completed_jobs / max(total_jobs, 1)),
            )

        # Get lead quality distribution if requested
        if "lead_quality" in request.metrics:
            companies_query = supabase.table("companies").select("lead_score")
            companies_query = companies_query.gte(
                "created_at", request.start_date.isoformat()
            )
            companies_query = companies_query.lte(
                "created_at", request.end_date.isoformat()
            )

            # Apply filters
            for key, value in query_filters.items():
                companies_query = companies_query.eq(key, value)

            companies_result = companies_query.execute()

            high_quality = 0
            medium_quality = 0
            low_quality = 0
            total_score = 0.0

            for company in companies_result.data:
                score = float(company.get("lead_score", 0))
                total_score += score

                if score >= 80:
                    high_quality += 1
                elif score >= 50:
                    medium_quality += 1
                else:
                    low_quality += 1

            total_leads = len(companies_result.data)
            avg_score = Decimal(total_score / max(total_leads, 1))

            lead_quality = LeadQualityDistribution(
                high_quality=high_quality,
                medium_quality=medium_quality,
                low_quality=low_quality,
                total_leads=total_leads,
                average_score=avg_score,
            )

        # Get contact insights if requested
        if "contact_insights" in request.metrics:
            contacts_query = supabase.table("contacts").select("*")
            contacts_query = contacts_query.gte(
                "created_at", request.start_date.isoformat()
            )
            contacts_query = contacts_query.lte(
                "created_at", request.end_date.isoformat()
            )
            contacts_result = contacts_query.execute()

            total_contacts = len(contacts_result.data)
            verified_contacts = len(
                [c for c in contacts_result.data if c.get("is_verified")]
            )
            decision_makers = len(
                [
                    c
                    for c in contacts_result.data
                    if c.get("seniority_level") in ["C-Level", "VP", "Director"]
                ]
            )
            contacts_with_email = len(
                [c for c in contacts_result.data if c.get("email")]
            )
            contacts_with_phone = len(
                [c for c in contacts_result.data if c.get("phone")]
            )
            contacts_with_linkedin = len(
                [c for c in contacts_result.data if c.get("linkedin_url")]
            )

            # Calculate job title distribution
            job_titles: Dict[str, int] = {}
            seniority_dist: Dict[str, int] = {}
            experience_years = []

            for contact in contacts_result.data:
                title = contact.get("job_title", "Unknown")
                job_titles[title] = job_titles.get(title, 0) + 1

                seniority = contact.get("seniority_level", "Unknown")
                seniority_dist[seniority] = seniority_dist.get(seniority, 0) + 1

                if contact.get("experience_years"):
                    experience_years.append(contact["experience_years"])

            top_job_titles: List[Dict[str, Union[str, int]]] = [
                {"title": str(k), "count": int(v)}
                for k, v in sorted(
                    job_titles.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            avg_experience = (
                sum(experience_years) / len(experience_years)
                if experience_years
                else None
            )

            contact_insights = ContactDataInsights(
                total_contacts=total_contacts,
                verified_contacts=verified_contacts,
                decision_makers=decision_makers,
                contacts_with_email=contacts_with_email,
                contacts_with_phone=contacts_with_phone,
                contacts_with_linkedin=contacts_with_linkedin,
                average_experience_years=avg_experience,
                top_job_titles=top_job_titles,
                seniority_distribution=seniority_dist,
            )

        # Get industry breakdown if requested
        if "industry_breakdown" in request.metrics:
            companies_query = supabase.table("companies").select(
                "industry", "company_size", "revenue_range"
            )
            companies_query = companies_query.gte(
                "created_at", request.start_date.isoformat()
            )
            companies_query = companies_query.lte(
                "created_at", request.end_date.isoformat()
            )
            companies_result = companies_query.execute()

            industry_dist: Dict[str, int] = {}
            company_size_dist: Dict[str, int] = {}
            revenue_dist: Dict[str, int] = {}

            for company in companies_result.data:
                industry = company.get("industry", "Unknown")
                industry_dist[industry] = industry_dist.get(industry, 0) + 1

                size = company.get("company_size", "Unknown")
                company_size_dist[size] = company_size_dist.get(size, 0) + 1

                revenue = company.get("revenue_range", "Unknown")
                revenue_dist[revenue] = revenue_dist.get(revenue, 0) + 1

            top_industries: List[Dict[str, Union[str, int]]] = [
                {"industry": str(k), "count": int(v)}
                for k, v in sorted(
                    industry_dist.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            industry_breakdown = IndustryBreakdown(
                industry_distribution=industry_dist,
                top_industries=top_industries,
                company_size_distribution=company_size_dist,
                revenue_distribution=revenue_dist,
            )

        # Get technology trends if requested
        if "technology_trends" in request.metrics:
            companies_query = supabase.table("companies").select("technology_stack")
            companies_query = companies_query.gte(
                "created_at", request.start_date.isoformat()
            )
            companies_query = companies_query.lte(
                "created_at", request.end_date.isoformat()
            )
            companies_result = companies_query.execute()

            tech_counts: Dict[str, int] = {}
            tech_combinations: Dict[str, int] = {}
            total_companies = len(companies_result.data)

            for company in companies_result.data:
                technologies = company.get("technology_stack", [])
                if isinstance(technologies, list):
                    for tech in technologies:
                        tech_counts[tech] = tech_counts.get(tech, 0) + 1

                    # Track technology combinations
                    if len(technologies) > 1:
                        combo_key = ",".join(sorted(technologies[:3]))  # Top 3 techs
                        tech_combinations[combo_key] = (
                            tech_combinations.get(combo_key, 0) + 1
                        )

            top_technologies: List[Dict[str, Union[str, int]]] = [
                {"technology": str(k), "count": int(v)}
                for k, v in sorted(
                    tech_counts.items(), key=lambda x: x[1], reverse=True
                )[:20]
            ]

            # Calculate adoption rates
            tech_adoption_rate = {
                tech: Decimal(count / max(total_companies, 1))
                for tech, count in tech_counts.items()
            }

            # Identify emerging technologies (low adoption but growing)
            emerging_techs = [
                tech
                for tech, rate in tech_adoption_rate.items()
                if 0.05 <= rate <= 0.20  # 5-20% adoption rate
            ][:10]

            top_combinations = [
                {"combination": k.split(","), "count": v}
                for k, v in sorted(
                    tech_combinations.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            technology_trends = TechnologyTrends(
                top_technologies=top_technologies,
                technology_adoption_rate=tech_adoption_rate,
                emerging_technologies=emerging_techs,
                technology_combinations=top_combinations,
            )

        return AnalyticsResponse(
            time_range=time_range,
            job_summary=job_summary,
            lead_quality=lead_quality,
            contact_insights=contact_insights,
            industry_breakdown=industry_breakdown,
            technology_trends=technology_trends,
        )

    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve comprehensive analytics"
        )


@router.get("/conversion-rates")
async def get_conversion_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = Query("day", regex="^(day|week|month)$"),
):
    """Get lead conversion rates over time"""
    try:
        # Set default date range
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        supabase = get_supabase_client()

        # Get companies with lead scores
        companies_result = (
            supabase.table("companies")
            .select("created_at", "lead_score", "industry")
            .gte("created_at", start_date)
            .lte("created_at", end_date)
            .execute()
        )

        # Group data by time period
        conversion_data = {}

        for company in companies_result.data:
            created_at = datetime.fromisoformat(
                company["created_at"].replace("Z", "+00:00")
            )
            lead_score = float(company.get("lead_score", 0))

            # Determine time grouping
            if group_by == "day":
                time_key = created_at.date().isoformat()
            elif group_by == "week":
                week_start = created_at - timedelta(days=created_at.weekday())
                time_key = week_start.date().isoformat()
            else:  # month
                time_key = f"{created_at.year}-{created_at.month:02d}"

            if time_key not in conversion_data:
                conversion_data[time_key] = {
                    "total_leads": 0,
                    "qualified_leads": 0,
                    "high_quality_leads": 0,
                }

            conversion_data[time_key]["total_leads"] += 1

            if lead_score >= 50:
                conversion_data[time_key]["qualified_leads"] += 1

            if lead_score >= 80:
                conversion_data[time_key]["high_quality_leads"] += 1

        # Calculate conversion rates
        result = []
        for time_key, data in sorted(conversion_data.items()):
            total = data["total_leads"]
            qualified_rate = (data["qualified_leads"] / max(total, 1)) * 100
            high_quality_rate = (data["high_quality_leads"] / max(total, 1)) * 100

            result.append(
                {
                    "period": time_key,
                    "total_leads": total,
                    "qualified_leads": data["qualified_leads"],
                    "high_quality_leads": data["high_quality_leads"],
                    "qualified_conversion_rate": round(qualified_rate, 2),
                    "high_quality_conversion_rate": round(high_quality_rate, 2),
                }
            )

        return {
            "conversion_rates": result,
            "summary": {
                "total_periods": len(result),
                "avg_qualified_rate": round(
                    sum(
                        float(r["qualified_conversion_rate"])
                        for r in result
                        if isinstance(r["qualified_conversion_rate"], (int, float))
                    )
                    / max(len(result), 1),
                    2,
                ),
                "avg_high_quality_rate": round(
                    sum(
                        float(r["high_quality_conversion_rate"])
                        for r in result
                        if isinstance(r["high_quality_conversion_rate"], (int, float))
                    )
                    / max(len(result), 1),
                    2,
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting conversion rates: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve conversion rates"
        )


@router.get("/data-quality")
async def get_data_quality_metrics(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    """Get data quality metrics and insights"""
    try:
        # Set default date range
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        supabase = get_supabase_client()

        # Get companies data
        companies_result = (
            supabase.table("companies")
            .select("*")
            .gte("created_at", start_date)
            .lte("created_at", end_date)
            .execute()
        )

        # Get contacts data
        contacts_result = (
            supabase.table("contacts")
            .select("*")
            .gte("created_at", start_date)
            .lte("created_at", end_date)
            .execute()
        )

        # Analyze company data quality
        company_metrics = {
            "total_companies": len(companies_result.data),
            "companies_with_description": 0,
            "companies_with_website": 0,
            "companies_with_industry": 0,
            "companies_with_size": 0,
            "companies_with_revenue": 0,
            "companies_with_technologies": 0,
            "avg_data_completeness": 0,
        }

        total_completeness = 0.0

        for company in companies_result.data:
            completeness_score = 0
            total_fields = 7  # Key fields to check

            if company.get("description"):
                company_metrics["companies_with_description"] += 1
                completeness_score += 1

            if company.get("website"):
                company_metrics["companies_with_website"] += 1
                completeness_score += 1

            if company.get("industry"):
                company_metrics["companies_with_industry"] += 1
                completeness_score += 1

            if company.get("company_size"):
                company_metrics["companies_with_size"] += 1
                completeness_score += 1

            if company.get("revenue_range"):
                company_metrics["companies_with_revenue"] += 1
                completeness_score += 1

            if company.get("technology_stack"):
                company_metrics["companies_with_technologies"] += 1
                completeness_score += 1

            if company.get("employee_count"):
                completeness_score += 1

            total_completeness += (completeness_score / total_fields) * 100

        if companies_result.data:
            company_metrics["avg_data_completeness"] = int(
                round(total_completeness / len(companies_result.data), 2)
            )

        # Analyze contact data quality
        contact_metrics = {
            "total_contacts": len(contacts_result.data),
            "contacts_with_email": 0,
            "contacts_with_phone": 0,
            "contacts_with_linkedin": 0,
            "contacts_with_title": 0,
            "verified_contacts": 0,
            "avg_data_completeness": 0,
        }

        total_contact_completeness = 0.0

        for contact in contacts_result.data:
            completeness_score = 0
            total_fields = 5  # Key fields to check

            if contact.get("email"):
                contact_metrics["contacts_with_email"] += 1
                completeness_score += 1

            if contact.get("phone"):
                contact_metrics["contacts_with_phone"] += 1
                completeness_score += 1

            if contact.get("linkedin_url"):
                contact_metrics["contacts_with_linkedin"] += 1
                completeness_score += 1

            if contact.get("job_title"):
                contact_metrics["contacts_with_title"] += 1
                completeness_score += 1

            if contact.get("is_verified"):
                contact_metrics["verified_contacts"] += 1
                completeness_score += 1

            total_contact_completeness += (completeness_score / total_fields) * 100

        if contacts_result.data:
            contact_metrics["avg_data_completeness"] = int(
                round(total_contact_completeness / len(contacts_result.data), 2)
            )

        # Calculate overall quality score
        overall_quality = {
            "company_data_quality": company_metrics["avg_data_completeness"],
            "contact_data_quality": contact_metrics["avg_data_completeness"],
            "overall_score": round(
                (
                    company_metrics["avg_data_completeness"]
                    + contact_metrics["avg_data_completeness"]
                )
                / 2,
                2,
            ),
        }

        return {
            "company_metrics": company_metrics,
            "contact_metrics": contact_metrics,
            "overall_quality": overall_quality,
            "recommendations": [
                "Focus on collecting company descriptions for better lead qualification",
                "Improve website data collection for better company insights",
                "Enhance contact verification processes",
                "Implement data enrichment for missing fields",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting data quality metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve data quality metrics"
        )


# ... existing code ...
