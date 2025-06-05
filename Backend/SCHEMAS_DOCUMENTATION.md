# Pydantic Models and Schemas Documentation

This document provides comprehensive documentation for all Pydantic models and schemas used in the Lead Generation SaaS backend system.

## Overview

The schema system is organized into three main files:

1. **`schemas.py`** - Core Pydantic schemas for data validation and serialization
2. **`api_schemas.py`** - API-specific schemas for request/response handling
3. **`database.py`** - SQLAlchemy database models

## Table of Contents

- [Base Schemas](#base-schemas)
- [Company Schemas](#company-schemas)
- [Contact Schemas](#contact-schemas)
- [Scraping Job Schemas](#scraping-job-schemas)
- [Scraped Data Schemas](#scraped-data-schemas)
- [Data Export Schemas](#data-export-schemas)
- [API Request/Response Schemas](#api-requestresponse-schemas)
- [Analytics Schemas](#analytics-schemas)
- [WebSocket Schemas](#websocket-schemas)
- [Usage Examples](#usage-examples)

## Base Schemas

### BaseSchema
Base schema with common configuration for all Pydantic models.

```python
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }
```

### TimestampMixin
Mixin for models with timestamp fields.

```python
class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime
```

### UserMixin
Mixin for models with user tracking.

```python
class UserMixin(BaseModel):
    created_by: UUID
```

### LocationSchema
Schema for location data used across multiple models.

```python
class LocationSchema(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
```

## Company Schemas

### CompanyBase
Base schema for company data with all core fields and validation.

**Key Features:**
- Name validation (1-255 characters)
- Website URL validation
- Founded year validation (1800-2030)
- Employee count validation (≥ 0)
- Score validation (0-1 for data quality, ≥ 0 for lead score)

### CompanyCreate
Schema for creating new companies. Inherits from `CompanyBase` and `UserMixin`.

### CompanyUpdate
Schema for updating existing companies. All fields are optional.

### CompanyResponse
Schema for company API responses. Includes additional computed fields:
- `contacts_count`: Number of associated contacts
- `scraped_data_count`: Number of associated scraped data records

### CompanyListResponse
Paginated response schema for company lists.

```python
class CompanyListResponse(BaseSchema):
    companies: List[CompanyResponse]
    total: int
    page: int
    size: int
    pages: int
```

## Contact Schemas

### ContactBase
Base schema for contact data with comprehensive validation.

**Key Features:**
- Email validation using `EmailStr`
- Twitter handle validation (auto-adds @ prefix)
- Experience years validation (0-70)
- Score validation (0-1 range)

### ContactCreate
Schema for creating new contacts.

### ContactUpdate
Schema for updating existing contacts. All fields are optional.

### ContactResponse
Schema for contact API responses. Includes nested company data.

### ContactListResponse
Paginated response schema for contact lists.

## Scraping Job Schemas

### ScrapingJobBase
Base schema for scraping jobs with validation.

**Validated Fields:**
- `job_type`: Must be one of `['google_my_business', 'linkedin', 'website', 'directory', 'custom']`
- `search_parameters`: Required dictionary with search criteria

### ScrapingJobCreate
Schema for creating new scraping jobs.

### ScrapingJobUpdate
Schema for updating scraping job status and progress.

**Validated Fields:**
- `status`: Must be one of `['pending', 'running', 'completed', 'failed', 'cancelled']`
- `progress_percentage`: 0-100 range

### ScrapingJobResponse
Comprehensive response schema with all job details and metrics.

### ScrapingJobListResponse
Paginated response schema for scraping job lists.

## Scraped Data Schemas

### ScrapedDataBase
Base schema for scraped data records.

**Validated Fields:**
- `source_type`: Must match job types
- `validation_status`: `['pending', 'valid', 'invalid', 'needs_review']`
- Confidence and completeness scores (0-1 range)

### ScrapedDataCreate
Schema for creating new scraped data records.

### ScrapedDataUpdate
Schema for updating scraped data processing status.

### ScrapedDataResponse
Response schema with nested job, company, and contact data.

## Data Export Schemas

### DataExportBase
Base schema for data export operations.

**Validated Fields:**
- `export_type`: `['csv', 'excel', 'json']`
- `export_name`: 1-255 characters

### DataExportCreate
Schema for creating new export jobs.

### DataExportUpdate
Schema for updating export status and file information.

### DataExportResponse
Response schema with download information and metrics.

## API Request/Response Schemas

### Search and Filtering

#### SearchFilters
Comprehensive filtering schema for searching companies and contacts.

```python
class SearchFilters(BaseSchema):
    query: Optional[str] = None
    industry: Optional[List[str]] = None
    company_size: Optional[List[str]] = None
    location: Optional[LocationSchema] = None
    # ... many more filters
```

#### PaginationParams
Standard pagination parameters.

```python
class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
```

#### SortParams
Sorting parameters with validation.

```python
class SortParams(BaseSchema):
    sort_by: str = Field(default='created_at')
    sort_order: str = Field(default='desc')  # 'asc' or 'desc'
```

### Scraping API Schemas

#### ScrapingSearchParameters
Detailed search parameters for scraping jobs.

```python
class ScrapingSearchParameters(BaseSchema):
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    location: Optional[LocationSchema] = None
    max_results: int = Field(default=100, ge=1, le=1000)
    include_contacts: bool = Field(default=True)
    contact_roles: Optional[List[str]] = None
    # ... additional parameters
```

#### ScrapingJobRequest
Request schema for creating scraping jobs.

```python
class ScrapingJobRequest(BaseSchema):
    job_name: str = Field(..., min_length=1, max_length=255)
    job_type: str = Field(...)  # Validated against allowed types
    search_parameters: ScrapingSearchParameters
    priority: str = Field(default='normal')  # 'low', 'normal', 'high', 'urgent'
    schedule_at: Optional[datetime] = None
    webhook_url: Optional[HttpUrl] = None
```

### Lead Search Schemas

#### LeadSearchFilters
Advanced filtering for lead searches with company and contact filters.

#### LeadSearchRequest
Comprehensive lead search request with filters, pagination, and options.

```python
class LeadSearchRequest(BaseSchema):
    filters: Optional[LeadSearchFilters] = None
    pagination: PaginationParams = PaginationParams()
    sort: SortParams = SortParams(sort_by='lead_score', sort_order='desc')
    include_contacts: bool = Field(default=True)
    include_score_breakdown: bool = Field(default=False)
    include_insights: bool = Field(default=False)
```

## Analytics Schemas

### JobSummaryAnalytics
Summary statistics for scraping jobs.

```python
class JobSummaryAnalytics(BaseSchema):
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    running_jobs: int = 0
    total_companies_found: int = 0
    total_contacts_found: int = 0
    average_completion_time: Optional[float] = None
    success_rate: Decimal = Field(ge=0, le=1)
```

### LeadQualityDistribution
Lead quality metrics and distribution.

### ContactDataInsights
Contact data completeness and insights.

### AnalyticsResponse
Comprehensive analytics response combining all metrics.

## WebSocket Schemas

### WebSocketMessage
Base schema for WebSocket messages.

```python
class WebSocketMessage(BaseSchema):
    type: str = Field(..., max_length=50)
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### JobProgressUpdate
Real-time job progress updates.

### LeadDiscoveryNotification
Notifications for new lead discoveries.

## Usage Examples

### Creating a Company

```python
from app.models import CompanyCreate
from uuid import uuid4

company_data = CompanyCreate(
    name="Tech Startup Inc.",
    domain="techstartup.com",
    website="https://www.techstartup.com",
    industry="Technology",
    company_size="11-50",
    location={
        "city": "San Francisco",
        "state": "CA",
        "country": "USA"
    },
    description="Innovative tech startup",
    founded_year=2020,
    employee_count=25,
    technology_stack=["Python", "React", "PostgreSQL"],
    created_by=uuid4()
)
```

### Creating a Scraping Job Request

```python
from app.models import ScrapingJobRequest, ScrapingSearchParameters

search_params = ScrapingSearchParameters(
    keywords=["software development", "tech startup"],
    location={
        "city": "San Francisco",
        "state": "CA",
        "country": "USA"
    },
    max_results=500,
    include_contacts=True,
    contact_roles=["CEO", "CTO", "VP Engineering"]
)

job_request = ScrapingJobRequest(
    job_name="SF Tech Startups",
    job_type="linkedin",
    search_parameters=search_params,
    priority="high"
)
```

### Lead Search Request

```python
from app.models import LeadSearchRequest, LeadSearchFilters, PaginationParams

filters = LeadSearchFilters(
    industry=["Technology", "Software"],
    company_size=["11-50", "51-200"],
    lead_score_min=70,
    has_email=True,
    is_decision_maker=True
)

search_request = LeadSearchRequest(
    filters=filters,
    pagination=PaginationParams(page=1, size=50),
    include_contacts=True,
    include_score_breakdown=True
)
```

### Analytics Request

```python
from app.models import AnalyticsRequest
from datetime import datetime, timedelta

analytics_request = AnalyticsRequest(
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow(),
    metrics=["job_summary", "lead_quality", "contact_insights"],
    group_by=["week", "industry"]
)
```

## Validation Features

### Automatic Validation
- **Email validation**: Uses `EmailStr` for proper email format validation
- **URL validation**: Uses `HttpUrl` for website and social media URLs
- **Range validation**: Numeric fields have appropriate min/max constraints
- **Enum validation**: String fields are validated against allowed values
- **Date validation**: Date fields include reasonable range constraints

### Custom Validators
- **Twitter handle**: Automatically adds @ prefix if missing
- **Job type validation**: Ensures job types match allowed scraping sources
- **Status validation**: Validates status transitions for jobs and data
- **Score validation**: Ensures scores are within valid ranges (0-1 or 0-100)

### Error Handling
All schemas include comprehensive error handling with descriptive messages:

```python
class ErrorResponse(BaseSchema):
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
```

## Best Practices

1. **Use appropriate base schemas**: Inherit from `BaseSchema` for consistent configuration
2. **Include mixins**: Use `TimestampMixin` and `UserMixin` where appropriate
3. **Validate inputs**: Always use create/update schemas for API inputs
4. **Use response schemas**: Use response schemas for API outputs to include computed fields
5. **Handle pagination**: Use `PaginationParams` and list response schemas for collections
6. **Include metadata**: Add timestamps, user tracking, and request IDs for debugging
7. **Validate enums**: Use validators for string fields with limited allowed values
8. **Document schemas**: Include docstrings and field descriptions for API documentation

## Integration with FastAPI

These schemas integrate seamlessly with FastAPI for automatic:
- Request validation
- Response serialization
- API documentation generation
- Error handling

```python
from fastapi import FastAPI
from app.models import CompanyCreate, CompanyResponse

app = FastAPI()

@app.post("/companies/", response_model=CompanyResponse)
async def create_company(company: CompanyCreate):
    # FastAPI automatically validates the request body
    # and serializes the response
    pass
```

This comprehensive schema system ensures data integrity, provides excellent developer experience, and enables automatic API documentation generation.