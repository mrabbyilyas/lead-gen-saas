from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
import math

from app.models.schemas import (
    LeadResponse,
    LeadListResponse,
    LeadScoreBreakdown,
    CompanyResponse,
    ContactResponse,
    CompanyUpdate,
    PaginationParams,
    SortParams,
)
from app.services.supabase_service import CompanyService, ContactService

# from app.services.data_processing.lead_scoring import (
#     create_lead_scoring_engine,
#     ScoreWeight,
# )  # TODO: Integrate when available
# from app.core.database import get_supabase_client  # TODO: Use when needed

router = APIRouter()
company_service = CompanyService()
contact_service = ContactService()


# Dependency to get current user (placeholder - implement based on your auth system)
async def get_current_user_id() -> str:
    """Get current user ID from authentication context."""
    # TODO: Implement proper user authentication
    # For now, return a placeholder user ID
    return "00000000-0000-0000-0000-000000000000"


@router.get("/", response_model=LeadListResponse)
async def get_leads(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company_size: Optional[str] = Query(None, description="Filter by company size"),
    min_score: Optional[float] = Query(None, ge=0, description="Minimum lead score"),
    max_score: Optional[float] = Query(None, ge=0, description="Maximum lead score"),
    sort_by: Optional[str] = Query(
        "lead_score", description="Sort field (lead_score, created_at, name)"
    ),
    sort_order: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort order"
    ),
    user_id: str = Depends(get_current_user_id),
):
    """Get leads with filtering, pagination, and sorting."""
    try:
        # Build filters
        filters = {"created_by": user_id}

        if industry:
            filters["industry"] = industry
        if company_size:
            filters["company_size"] = company_size
        if location:
            # Handle location filtering (assuming JSON field)
            filters["location"] = location
        if min_score is not None or max_score is not None:
            score_filter = {}
            if min_score is not None:
                score_filter["gte"] = min_score
            if max_score is not None:
                score_filter["lte"] = max_score
            filters["lead_score"] = str(score_filter)

        # Set up pagination and sorting
        pagination = PaginationParams(page=page, page_size=size)
        sort_params = SortParams(
            sort_by=sort_by or "created_at", sort_order=sort_order or "desc"
        )

        # Get companies (leads)
        companies, total = company_service.get_companies_by_user(
            user_id=user_id,
            filters=filters,
            pagination=pagination,
            sort_params=sort_params,
        )

        # Build lead responses with contacts and scoring
        leads = []
        for company in companies:
            # Get contacts for this company
            contacts, _ = contact_service.get_contacts_by_company(company_id=company.id)

            # Calculate lead score breakdown
            lead_score_breakdown = _calculate_lead_score_breakdown(
                company.model_dump(), [contact.model_dump() for contact in contacts]
            )

            # Generate insights and recommendations
            insights = _generate_insights(company, contacts)
            recommendations = _generate_recommendations(company, contacts)

            lead = LeadResponse(
                company=company,
                contacts=contacts,
                lead_score_breakdown=lead_score_breakdown,
                insights=insights,
                recommendations=recommendations,
            )
            leads.append(lead)

        # Calculate pagination info
        pages = math.ceil(total / size) if total > 0 else 1

        # Generate summary statistics
        summary = _generate_summary_stats(leads, total)

        return LeadListResponse(
            leads=leads,
            total=total,
            page=page,
            size=size,
            pages=pages,
            summary=summary,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve leads: {str(e)}"
        )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get detailed information for a specific lead."""
    try:
        # Get company (lead)
        company = company_service.get_company(lead_id)
        if not company:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Verify ownership
        if str(company.created_by) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get contacts for this company
        contacts, _ = contact_service.get_contacts_by_company(company_id=lead_id)

        # Calculate detailed lead score breakdown
        lead_score_breakdown = _calculate_lead_score_breakdown(
            company.model_dump(), [contact.model_dump() for contact in contacts]
        )

        # Generate detailed insights and recommendations
        insights = _generate_detailed_insights(company, contacts)
        recommendations = _generate_detailed_recommendations(company, contacts)

        return LeadResponse(
            company=company,
            contacts=contacts,
            lead_score_breakdown=lead_score_breakdown,
            insights=insights,
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve lead: {str(e)}"
        )


@router.put("/{lead_id}/score", response_model=LeadResponse)
async def recalculate_lead_score(
    lead_id: str,
    weights: Optional[Dict[str, float]] = None,
    user_id: str = Depends(get_current_user_id),
):
    """Recalculate lead score with optional custom weights."""
    try:
        # Get company (lead)
        company = company_service.get_company(lead_id)
        if not company:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Verify ownership
        if str(company.created_by) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get contacts for this company
        contacts, _ = contact_service.get_contacts_by_company(company_id=lead_id)

        # TODO: Implement custom score weights when scoring engine is available
        # Create custom score weights if provided
        # score_weights = None
        # if weights:
        #     score_weights = ScoreWeight(
        #         contact_completeness=weights.get("contact_completeness", 0.25),
        #         business_indicators=weights.get("business_indicators", 0.30),
        #         data_quality=weights.get("data_quality", 0.20),
        #         engagement_potential=weights.get("engagement_potential", 0.25),
        #     )

        # Recalculate lead score
        # scoring_engine = create_lead_scoring_engine(score_weights)
        # lead_score = scoring_engine.score_lead(
        #     company.model_dump(), [contact.model_dump() for contact in contacts]
        # )

        # Mock lead score calculation for now
        mock_total_score = 77.5
        if weights:
            # Adjust mock score based on weights
            mock_total_score = sum(
                [
                    75.0 * weights.get("contact_completeness", 0.25),
                    80.0 * weights.get("business_indicators", 0.30),
                    70.0 * weights.get("data_quality", 0.20),
                    85.0 * weights.get("engagement_potential", 0.25),
                ]
            )

        # Update company with new score
        company_update = CompanyUpdate.model_validate(
            {"lead_score": Decimal(str(mock_total_score))}
        )
        updated_company = company_service.update_company(lead_id, company_update)

        if not updated_company:
            raise HTTPException(status_code=500, detail="Failed to update lead score")

        # Calculate updated lead score breakdown
        lead_score_breakdown = LeadScoreBreakdown(
            contact_completeness=Decimal("75.0"),
            business_indicators=Decimal("80.0"),
            data_quality=Decimal("70.0"),
            engagement_potential=Decimal("85.0"),
            total_score=Decimal(str(mock_total_score)),
            score_factors={
                "company_size": "medium",
                "industry_match": True,
                "contact_quality": "high",
                "data_completeness": 0.75,
                "custom_weights_applied": bool(weights),
            },
        )

        # Generate updated insights and recommendations
        insights = _generate_detailed_insights(updated_company, contacts)
        recommendations = _generate_detailed_recommendations(updated_company, contacts)

        return LeadResponse(
            company=updated_company,
            contacts=contacts,
            lead_score_breakdown=lead_score_breakdown,
            insights=insights,
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to recalculate lead score: {str(e)}"
        )


@router.get("/export/csv")
async def export_leads_csv(
    industry: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    company_size: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0),
    max_score: Optional[float] = Query(None, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    """Export leads to CSV format."""
    try:
        # Build filters (same as get_leads)
        filters = {"created_by": user_id}

        if industry:
            filters["industry"] = industry
        if company_size:
            filters["company_size"] = company_size
        if location:
            filters["location"] = location
        if min_score is not None or max_score is not None:
            score_filter = {}
            if min_score is not None:
                score_filter["gte"] = min_score
            if max_score is not None:
                score_filter["lte"] = max_score
            filters["lead_score"] = str(score_filter)

        # Get all companies without pagination for export
        companies, total = company_service.get_companies_by_user(
            user_id=user_id, filters=filters
        )

        # Generate CSV content
        csv_content = _generate_csv_export(companies)

        return {
            "csv_content": csv_content,
            "total_records": total,
            "filename": f"leads_export_{user_id}_{int(datetime.now().timestamp())}.csv",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export leads: {str(e)}")


# Helper functions


def _calculate_lead_score_breakdown(
    company_data: Dict[str, Any], contacts_data: List[Dict[str, Any]]
) -> LeadScoreBreakdown:
    """Calculate lead score breakdown using the scoring engine."""
    # TODO: Implement proper lead scoring integration
    # For now, return a mock score breakdown until the scoring engine is properly integrated
    return LeadScoreBreakdown(
        contact_completeness=Decimal("75.0"),
        business_indicators=Decimal("80.0"),
        data_quality=Decimal("70.0"),
        engagement_potential=Decimal("85.0"),
        total_score=Decimal("77.5"),
        score_factors={
            "company_size": "medium",
            "industry_match": True,
            "contact_quality": "high",
            "data_completeness": 0.75,
        },
    )


def _generate_insights(
    company: CompanyResponse, contacts: List[ContactResponse]
) -> Dict[str, Any]:
    """Generate basic insights for a lead."""
    return {
        "contact_count": len(contacts),
        "decision_makers": len([c for c in contacts if c.is_decision_maker]),
        "verified_contacts": len([c for c in contacts if c.is_verified]),
        "has_website": bool(company.website),
        "has_social_media": bool(company.social_media),
        "technology_count": len(company.technology_stack or []),
        "growth_signals_count": len(
            [k for k, v in (company.growth_signals or {}).items() if v]
        ),
    }


def _generate_recommendations(
    company: CompanyResponse, contacts: List[ContactResponse]
) -> List[str]:
    """Generate basic recommendations for a lead."""
    recommendations = []

    if not contacts:
        recommendations.append("Find and add contact information for this company")
    elif len(contacts) < 3:
        recommendations.append("Expand contact database for better coverage")

    if not any(c.is_decision_maker for c in contacts):
        recommendations.append("Identify decision makers within the organization")

    if not company.website:
        recommendations.append("Research and add company website information")

    if not company.social_media:
        recommendations.append("Find company social media profiles")

    if company.lead_score and company.lead_score < 50:
        recommendations.append("Focus on data enrichment to improve lead quality")

    return recommendations


def _generate_detailed_insights(
    company: CompanyResponse, contacts: List[ContactResponse]
) -> Dict[str, Any]:
    """Generate detailed insights for a lead."""
    insights = _generate_insights(company, contacts)

    # Add detailed analysis
    insights.update(
        {
            "contact_quality_avg": (
                sum(c.contact_quality_score or 0 for c in contacts) / len(contacts)
                if contacts
                else 0
            ),
            "engagement_potential_avg": (
                sum(c.engagement_potential or 0 for c in contacts) / len(contacts)
                if contacts
                else 0
            ),
            "seniority_distribution": _analyze_seniority_distribution(contacts),
            "department_coverage": _analyze_department_coverage(contacts),
            "data_completeness": _analyze_data_completeness(company, contacts),
            "competitive_analysis": _analyze_competitive_landscape(company),
        }
    )

    return insights


def _generate_detailed_recommendations(
    company: CompanyResponse, contacts: List[ContactResponse]
) -> List[str]:
    """Generate detailed recommendations for a lead."""
    recommendations = _generate_recommendations(company, contacts)

    # Add detailed recommendations based on analysis
    if contacts:
        avg_quality = sum(c.contact_quality_score or 0 for c in contacts) / len(
            contacts
        )
        if avg_quality < 0.7:
            recommendations.append(
                "Improve contact data quality through verification and enrichment"
            )

    if company.pain_points:
        recommendations.append("Leverage identified pain points in outreach messaging")

    if company.growth_signals:
        active_signals = [k for k, v in company.growth_signals.items() if v]
        if active_signals:
            recommendations.append(
                f"Capitalize on growth signals: {', '.join(active_signals)}"
            )

    return recommendations


def _generate_summary_stats(leads: List[LeadResponse], total: int) -> Dict[str, Any]:
    """Generate summary statistics for the lead list."""
    if not leads:
        return {"total_leads": total, "avg_score": 0, "score_distribution": {}}

    scores = [lead.lead_score_breakdown.total_score for lead in leads]
    avg_score = sum(scores) / len(scores)

    # Score distribution
    score_ranges = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    for score in scores:
        if score <= 25:
            score_ranges["0-25"] += 1
        elif score <= 50:
            score_ranges["26-50"] += 1
        elif score <= 75:
            score_ranges["51-75"] += 1
        else:
            score_ranges["76-100"] += 1

    return {
        "total_leads": total,
        "avg_score": round(avg_score, 2),
        "score_distribution": score_ranges,
        "industries": list(
            set(lead.company.industry for lead in leads if lead.company.industry)
        ),
        "company_sizes": list(
            set(
                lead.company.company_size for lead in leads if lead.company.company_size
            )
        ),
    }


def _analyze_seniority_distribution(contacts: List[ContactResponse]) -> Dict[str, int]:
    """Analyze seniority level distribution of contacts."""
    distribution: Dict[str, int] = {}
    for contact in contacts:
        level = contact.seniority_level or "Unknown"
        distribution[level] = distribution.get(level, 0) + 1
    return distribution


def _analyze_department_coverage(contacts: List[ContactResponse]) -> Dict[str, float]:
    """Analyze department coverage of contacts."""
    coverage: Dict[str, float] = {}
    total_contacts = len(contacts)
    if total_contacts == 0:
        return coverage

    dept_counts: Dict[str, int] = {}
    for contact in contacts:
        dept = contact.department or "Unknown"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Convert to percentages
    for dept, count in dept_counts.items():
        coverage[dept] = (count / total_contacts) * 100

    return coverage


def _analyze_data_completeness(
    company: CompanyResponse, contacts: List[ContactResponse]
) -> Dict[str, float]:
    """Analyze data completeness for company and contacts."""
    company_fields = [
        "name",
        "domain",
        "website",
        "industry",
        "company_size",
        "location",
    ]
    company_completeness = sum(
        1 for field in company_fields if getattr(company, field, None)
    ) / len(company_fields)

    if contacts:
        contact_fields = ["first_name", "last_name", "email", "job_title", "department"]
        contact_completeness = sum(
            sum(1 for field in contact_fields if getattr(contact, field, None))
            / len(contact_fields)
            for contact in contacts
        ) / len(contacts)
    else:
        contact_completeness = 0

    return {
        "company_completeness": round(company_completeness, 2),
        "contact_completeness": round(contact_completeness, 2),
        "overall_completeness": round(
            (company_completeness + contact_completeness) / 2, 2
        ),
    }


def _analyze_competitive_landscape(company: CompanyResponse) -> Dict[str, Any]:
    """Analyze competitive landscape information."""
    if not company.competitive_landscape:
        return {"competitors_identified": 0, "market_position": "Unknown"}

    competitors = company.competitive_landscape or []
    return {
        "competitors_identified": len(competitors),
        "market_position": "Analyzed" if competitors else "Unknown",
        "competitive_advantages": len(
            [c for c in competitors if isinstance(c, dict) and c.get("advantages")]
        ),
    }


def _generate_csv_export(companies: List[CompanyResponse]) -> str:
    """Generate CSV content for lead export."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Company ID",
            "Company Name",
            "Domain",
            "Website",
            "Industry",
            "Company Size",
            "Location",
            "Lead Score",
            "Data Quality Score",
            "Employee Count",
            "Founded Year",
            "Revenue Range",
            "Created At",
        ]
    )

    # Write data
    for company in companies:
        location_str = ""
        if company.location:
            if isinstance(company.location, dict):
                location_parts = []
                if company.location.get("city"):
                    location_parts.append(company.location["city"])
                if company.location.get("state"):
                    location_parts.append(company.location["state"])
                if company.location.get("country"):
                    location_parts.append(company.location["country"])
                location_str = ", ".join(location_parts)

        writer.writerow(
            [
                str(company.id),
                company.name or "",
                company.domain or "",
                company.website or "",
                company.industry or "",
                company.company_size or "",
                location_str,
                company.lead_score or 0,
                company.data_quality_score or 0,
                company.employee_count or "",
                company.founded_year or "",
                company.revenue_range or "",
                company.created_at.isoformat() if company.created_at else "",
            ]
        )

    return output.getvalue()
