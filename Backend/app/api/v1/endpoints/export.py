import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.api_schemas import ExportRequest
from app.models.schemas import (
    CompanyResponse,
    ContactResponse,
    PaginationParams,
    SortParams,
)
from app.services.supabase_service import CompanyService, ContactService

logger = logging.getLogger(__name__)
router = APIRouter()


# Available export fields for different data types
COMPANY_EXPORT_FIELDS = {
    "basic": [
        "id",
        "name",
        "domain",
        "website",
        "industry",
        "company_size",
        "employee_count",
    ],
    "contact_info": ["phone", "address", "location"],
    "business_data": [
        "founded_year",
        "revenue_range",
        "description",
        "technology_stack",
        "social_media",
    ],
    "analytics": [
        "lead_score",
        "data_quality_score",
        "growth_signals",
        "pain_points",
        "competitive_landscape",
    ],
    "metadata": ["created_at", "updated_at", "contacts_count", "scraped_data_count"],
}

CONTACT_EXPORT_FIELDS = {
    "basic": ["id", "first_name", "last_name", "full_name", "email", "phone"],
    "professional": [
        "job_title",
        "department",
        "seniority_level",
        "experience_years",
        "skills",
    ],
    "social": ["linkedin_url", "twitter_handle", "bio"],
    "analytics": [
        "contact_quality_score",
        "engagement_potential",
        "is_decision_maker",
        "is_verified",
    ],
    "metadata": ["created_at", "updated_at", "last_activity_date"],
}


def get_company_service() -> CompanyService:
    """Dependency to get Company service."""
    return CompanyService()


def get_contact_service() -> ContactService:
    """Dependency to get Contact service."""
    return ContactService()


@router.post("/csv", response_class=StreamingResponse)
async def export_to_csv(
    request: ExportRequest,
    company_service: CompanyService = Depends(get_company_service),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Export data to CSV format with selective fields and filtering."""
    try:
        # Validate export request
        if request.data_type not in ["companies", "contacts", "leads"]:
            raise HTTPException(
                status_code=400, detail="Invalid data_type for CSV export"
            )

        # Get data based on type
        if request.data_type in ["companies", "leads"]:
            companies_data = await _get_companies_data(
                company_service, request.filters, request.max_records
            )
            csv_content = _generate_companies_csv(
                companies_data, request.fields, request.include_headers
            )
            filename = (
                f"companies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        else:  # contacts
            contacts_data = await _get_contacts_data(
                contact_service, request.filters, request.max_records
            )
            csv_content = _generate_contacts_csv(
                contacts_data, request.fields, request.include_headers
            )
            filename = f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Create streaming response
        def iter_csv():
            yield csv_content

        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/excel")
async def export_to_excel(
    request: ExportRequest,
    company_service: CompanyService = Depends(get_company_service),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Export data to Excel format (placeholder for future implementation)."""
    # For now, return CSV as Excel is more complex to implement
    return await export_to_csv(request, company_service, contact_service)


@router.post("/json", response_class=StreamingResponse)
async def export_to_json(
    request: ExportRequest,
    company_service: CompanyService = Depends(get_company_service),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Export data to JSON format."""
    try:
        # Get data based on type
        if request.data_type in ["companies", "leads"]:
            companies_data = await _get_companies_data(
                company_service, request.filters, request.max_records
            )
            json_data = _filter_fields_from_companies(companies_data, request.fields)
        else:  # contacts
            contacts_data = await _get_contacts_data(
                contact_service, request.filters, request.max_records
            )
            json_data = _filter_fields_from_contacts(contacts_data, request.fields)

        # Convert to JSON string
        json_content = json.dumps(json_data, indent=2, default=str)
        filename = f"{request.data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        def iter_json():
            yield json_content

        return StreamingResponse(
            iter_json(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"JSON export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/fields/{data_type}")
async def get_available_fields(data_type: str):
    """Get available fields for export by data type."""
    if data_type == "companies":
        return {"available_fields": COMPANY_EXPORT_FIELDS}
    elif data_type == "contacts":
        return {"available_fields": CONTACT_EXPORT_FIELDS}
    else:
        raise HTTPException(status_code=400, detail="Invalid data type")


@router.post("/crm/salesforce")
async def export_to_salesforce(
    request: ExportRequest,
    salesforce_config: Dict[str, Any],
    company_service: CompanyService = Depends(get_company_service),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Export data to Salesforce CRM (placeholder for integration)."""
    # This would integrate with Salesforce API
    return {
        "message": "Salesforce integration - to be implemented",
        "status": "pending",
        "integration_type": "salesforce",
        "record_count": 0,
    }


@router.post("/crm/hubspot")
async def export_to_hubspot(
    request: ExportRequest,
    hubspot_config: Dict[str, Any],
    company_service: CompanyService = Depends(get_company_service),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Export data to HubSpot CRM (placeholder for integration)."""
    # This would integrate with HubSpot API
    return {
        "message": "HubSpot integration - to be implemented",
        "status": "pending",
        "integration_type": "hubspot",
        "record_count": 0,
    }


@router.post("/crm/pipedrive")
async def export_to_pipedrive(
    request: ExportRequest,
    pipedrive_config: Dict[str, Any],
    company_service: CompanyService = Depends(get_company_service),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Export data to Pipedrive CRM (placeholder for integration)."""
    # This would integrate with Pipedrive API
    return {
        "message": "Pipedrive integration - to be implemented",
        "status": "pending",
        "integration_type": "pipedrive",
        "record_count": 0,
    }


@router.get("/history")
async def get_export_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    company_service: CompanyService = Depends(get_company_service),
):
    """Get export history with pagination."""
    try:
        # This would fetch export history from database
        # For now, return placeholder data
        return {
            "exports": [],
            "total": 0,
            "page": page,
            "size": size,
            "pages": 0,
        }
    except Exception as e:
        logger.error(f"Export history error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get export history: {str(e)}"
        )


# Helper functions
async def _get_companies_data(
    company_service: CompanyService,
    filters: Optional[Dict[str, Any]] = None,
    max_records: Optional[int] = None,
) -> List[CompanyResponse]:
    """Get companies data with optional filtering."""
    try:
        # Build pagination params
        pagination = PaginationParams(page=1, size=max_records or 1000)

        # Build sort params
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Get companies from database - using get_companies_by_user method
        user_id = "00000000-0000-0000-0000-000000000000"  # TODO: Get from auth
        companies, total = company_service.get_companies_by_user(
            user_id=user_id, filters=filters, pagination=pagination, sort_params=sort
        )

        return companies
    except Exception as e:
        logger.error(f"Error fetching companies data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch companies: {str(e)}"
        )


async def _get_contacts_data(
    contact_service: ContactService,
    filters: Optional[Dict[str, Any]] = None,
    max_records: Optional[int] = None,
) -> List[ContactResponse]:
    """Get contacts data with optional filtering."""
    try:
        # Build pagination params
        pagination = PaginationParams(page=1, size=max_records or 1000)

        # Build sort params
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Get contacts from database - using get_contacts_by_user method
        user_id = "00000000-0000-0000-0000-000000000000"  # TODO: Get from auth
        contacts, total = contact_service.get_contacts_by_user(
            user_id=user_id, filters=filters, pagination=pagination, sort_params=sort
        )

        return contacts
    except Exception as e:
        logger.error(f"Error fetching contacts data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch contacts: {str(e)}"
        )


def _generate_companies_csv(
    companies: List[CompanyResponse],
    selected_fields: Optional[List[str]] = None,
    include_headers: bool = True,
) -> str:
    """Generate CSV content for companies export."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Determine fields to export
    if selected_fields:
        fields = selected_fields
    else:
        # Default fields
        fields = [
            "id",
            "name",
            "domain",
            "website",
            "industry",
            "company_size",
            "employee_count",
            "founded_year",
            "revenue_range",
            "lead_score",
            "data_quality_score",
            "location",
            "created_at",
        ]

    # Write header
    if include_headers:
        headers = [field.replace("_", " ").title() for field in fields]
        writer.writerow(headers)

    # Write data
    for company in companies:
        row = []
        for field in fields:
            value = getattr(company, field, None)

            # Handle special field formatting
            if field == "location" and value:
                if isinstance(value, dict):
                    location_parts = []
                    for key in ["city", "state", "country"]:
                        if value.get(key):
                            location_parts.append(value[key])
                    value = ", ".join(location_parts)
            elif (
                field in ["technology_stack", "pain_points", "competitive_landscape"]
                and value
            ):
                if isinstance(value, list):
                    value = "; ".join(str(item) for item in value)
            elif field == "social_media" and value:
                if isinstance(value, dict):
                    social_links = []
                    for platform, url in value.items():
                        social_links.append(f"{platform}: {url}")
                    value = "; ".join(social_links)
            elif field == "growth_signals" and value:
                if isinstance(value, dict):
                    signals = []
                    for signal, data in value.items():
                        signals.append(f"{signal}: {data}")
                    value = "; ".join(signals)
            elif value is not None and hasattr(value, "isoformat"):  # datetime objects
                value = value.isoformat()

            row.append(str(value) if value is not None else "")

        writer.writerow(row)

    return output.getvalue()


def _generate_contacts_csv(
    contacts: List[ContactResponse],
    selected_fields: Optional[List[str]] = None,
    include_headers: bool = True,
) -> str:
    """Generate CSV content for contacts export."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Determine fields to export
    if selected_fields:
        fields = selected_fields
    else:
        # Default fields
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "job_title",
            "department",
            "seniority_level",
            "linkedin_url",
            "contact_quality_score",
            "engagement_potential",
            "is_decision_maker",
            "is_verified",
            "created_at",
        ]

    # Write header
    if include_headers:
        headers = [field.replace("_", " ").title() for field in fields]
        writer.writerow(headers)

    # Write data
    for contact in contacts:
        row = []
        for field in fields:
            value = getattr(contact, field, None)

            # Handle special field formatting
            if field == "skills" and value:
                if isinstance(value, list):
                    value = "; ".join(value)
            elif field == "education" and value:
                if isinstance(value, list):
                    education_items = []
                    for edu in value:
                        if isinstance(edu, dict):
                            edu_str = f"{edu.get('degree', '')} at {edu.get('institution', '')}"
                            education_items.append(edu_str.strip())
                    value = "; ".join(education_items)
            elif value is not None and hasattr(value, "isoformat"):  # datetime objects
                value = value.isoformat()

            row.append(str(value) if value is not None else "")

        writer.writerow(row)

    return output.getvalue()


def _filter_fields_from_companies(
    companies: List[CompanyResponse],
    selected_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter and format company data for JSON export."""
    result = []

    for company in companies:
        company_dict = company.dict()

        if selected_fields:
            # Filter to only selected fields
            filtered_dict = {}
            for field in selected_fields:
                if field in company_dict:
                    filtered_dict[field] = company_dict[field]
            result.append(filtered_dict)
        else:
            result.append(company_dict)

    return result


def _filter_fields_from_contacts(
    contacts: List[ContactResponse],
    selected_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter and format contact data for JSON export."""
    result = []

    for contact in contacts:
        contact_dict = contact.dict()

        if selected_fields:
            # Filter to only selected fields
            filtered_dict = {}
            for field in selected_fields:
                if field in contact_dict:
                    filtered_dict[field] = contact_dict[field]
            result.append(filtered_dict)
        else:
            result.append(contact_dict)

    return result


@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    company_service: CompanyService = Depends(get_company_service),
):
    """Download a previously generated export"""
    try:
        # This would fetch the export file from storage
        # For now, return a placeholder response
        raise HTTPException(
            status_code=404, detail=f"Export {export_id} not found or has expired"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download export error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to download export: {str(e)}"
        )
