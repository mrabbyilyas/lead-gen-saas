from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator


# ============================================================================
# Base Schemas
# ============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""
    created_at: datetime
    updated_at: datetime


class UserMixin(BaseModel):
    """Mixin for models with user tracking."""
    created_by: UUID


# ============================================================================
# Location Schema
# ============================================================================

class LocationSchema(BaseModel):
    """Schema for location data."""
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ============================================================================
# Company Schemas
# ============================================================================

class CompanyBase(BaseSchema):
    """Base company schema."""
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    website: Optional[HttpUrl] = None
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    location: Optional[LocationSchema] = None
    description: Optional[str] = None
    founded_year: Optional[int] = Field(None, ge=1800, le=2030)
    revenue_range: Optional[str] = Field(None, max_length=50)
    technology_stack: Optional[List[str]] = None
    social_media: Optional[Dict[str, str]] = None
    employee_count: Optional[int] = Field(None, ge=0)
    growth_signals: Optional[Dict[str, Any]] = None
    pain_points: Optional[List[str]] = None
    competitive_landscape: Optional[List[str]] = None
    data_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    lead_score: Optional[Decimal] = Field(None, ge=0)


class CompanyCreate(CompanyBase, UserMixin):
    """Schema for creating a company."""
    pass


class CompanyUpdate(BaseSchema):
    """Schema for updating a company."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    website: Optional[HttpUrl] = None
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    location: Optional[LocationSchema] = None
    description: Optional[str] = None
    founded_year: Optional[int] = Field(None, ge=1800, le=2030)
    revenue_range: Optional[str] = Field(None, max_length=50)
    technology_stack: Optional[List[str]] = None
    social_media: Optional[Dict[str, str]] = None
    employee_count: Optional[int] = Field(None, ge=0)
    growth_signals: Optional[Dict[str, Any]] = None
    pain_points: Optional[List[str]] = None
    competitive_landscape: Optional[List[str]] = None
    data_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    lead_score: Optional[Decimal] = Field(None, ge=0)


class CompanyResponse(CompanyBase, TimestampMixin, UserMixin):
    """Schema for company response."""
    id: UUID
    contacts_count: Optional[int] = 0
    scraped_data_count: Optional[int] = 0


class CompanyListResponse(BaseSchema):
    """Schema for company list response."""
    companies: List[CompanyResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Contact Schemas
# ============================================================================

class ContactBase(BaseSchema):
    """Base contact schema."""
    company_id: Optional[UUID] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    seniority_level: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    location: Optional[LocationSchema] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=70)
    education: Optional[List[Dict[str, Any]]] = None
    contact_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    engagement_potential: Optional[Decimal] = Field(None, ge=0, le=1)
    last_activity_date: Optional[datetime] = None
    is_decision_maker: Optional[bool] = False
    is_verified: Optional[bool] = False

    @validator('twitter_handle')
    def validate_twitter_handle(cls, v):
        if v and not v.startswith('@'):
            v = f'@{v}'
        return v


class ContactCreate(ContactBase, UserMixin):
    """Schema for creating a contact."""
    pass


class ContactUpdate(BaseSchema):
    """Schema for updating a contact."""
    company_id: Optional[UUID] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    seniority_level: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    location: Optional[LocationSchema] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=70)
    education: Optional[List[Dict[str, Any]]] = None
    contact_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    engagement_potential: Optional[Decimal] = Field(None, ge=0, le=1)
    last_activity_date: Optional[datetime] = None
    is_decision_maker: Optional[bool] = None
    is_verified: Optional[bool] = None


class ContactResponse(ContactBase, TimestampMixin, UserMixin):
    """Schema for contact response."""
    id: UUID
    company: Optional[CompanyResponse] = None


class ContactListResponse(BaseSchema):
    """Schema for contact list response."""
    contacts: List[ContactResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Scraping Job Schemas
# ============================================================================

class ScrapingJobBase(BaseSchema):
    """Base scraping job schema."""
    job_name: str = Field(..., min_length=1, max_length=255)
    job_type: str = Field(..., max_length=50)
    search_parameters: Dict[str, Any] = Field(...)
    source_urls: Optional[List[str]] = None

    @validator('job_type')
    def validate_job_type(cls, v):
        allowed_types = ['google_my_business', 'linkedin', 'website', 'directory', 'custom']
        if v not in allowed_types:
            raise ValueError(f'job_type must be one of: {", ".join(allowed_types)}')
        return v


class ScrapingJobCreate(ScrapingJobBase, UserMixin):
    """Schema for creating a scraping job."""
    pass


class ScrapingJobUpdate(BaseSchema):
    """Schema for updating a scraping job."""
    job_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    progress_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    total_targets: Optional[int] = Field(None, ge=0)
    processed_targets: Optional[int] = Field(None, ge=0)
    successful_extractions: Optional[int] = Field(None, ge=0)
    failed_extractions: Optional[int] = Field(None, ge=0)
    companies_found: Optional[int] = Field(None, ge=0)
    contacts_found: Optional[int] = Field(None, ge=0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
            if v not in allowed_statuses:
                raise ValueError(f'status must be one of: {", ".join(allowed_statuses)}')
        return v


class ScrapingJobResponse(ScrapingJobBase, TimestampMixin, UserMixin):
    """Schema for scraping job response."""
    id: UUID
    status: str = 'pending'
    progress_percentage: Decimal = Decimal('0.00')
    total_targets: int = 0
    processed_targets: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    companies_found: int = 0
    contacts_found: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class ScrapingJobListResponse(BaseSchema):
    """Schema for scraping job list response."""
    jobs: List[ScrapingJobResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Scraped Data Schemas
# ============================================================================

class ScrapedDataBase(BaseSchema):
    """Base scraped data schema."""
    job_id: UUID
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    source_type: str = Field(..., max_length=50)
    source_url: Optional[str] = Field(None, max_length=1000)
    raw_data: Dict[str, Any] = Field(...)
    processed_data: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    data_completeness: Optional[Decimal] = Field(None, ge=0, le=1)
    validation_status: str = Field(default='pending', max_length=50)
    validation_errors: Optional[List[str]] = None
    duplicate_of: Optional[UUID] = None
    is_processed: bool = False
    processing_notes: Optional[str] = None
    scraped_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    @validator('source_type')
    def validate_source_type(cls, v):
        allowed_types = ['google_my_business', 'linkedin', 'website', 'directory', 'custom']
        if v not in allowed_types:
            raise ValueError(f'source_type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('validation_status')
    def validate_validation_status(cls, v):
        allowed_statuses = ['pending', 'valid', 'invalid', 'needs_review']
        if v not in allowed_statuses:
            raise ValueError(f'validation_status must be one of: {", ".join(allowed_statuses)}')
        return v


class ScrapedDataCreate(ScrapedDataBase):
    """Schema for creating scraped data."""
    pass


class ScrapedDataUpdate(BaseSchema):
    """Schema for updating scraped data."""
    processed_data: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    data_completeness: Optional[Decimal] = Field(None, ge=0, le=1)
    validation_status: Optional[str] = Field(None, max_length=50)
    validation_errors: Optional[List[str]] = None
    is_processed: Optional[bool] = None
    processing_notes: Optional[str] = None
    processed_at: Optional[datetime] = None


class ScrapedDataResponse(ScrapedDataBase, TimestampMixin):
    """Schema for scraped data response."""
    id: UUID
    scraping_job: Optional[ScrapingJobResponse] = None
    company: Optional[CompanyResponse] = None
    contact: Optional[ContactResponse] = None


class ScrapedDataListResponse(BaseSchema):
    """Schema for scraped data list response."""
    scraped_data: List[ScrapedDataResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Data Export Schemas
# ============================================================================

class DataExportBase(BaseSchema):
    """Base data export schema."""
    export_name: str = Field(..., min_length=1, max_length=255)
    export_type: str = Field(..., max_length=50)
    filters: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

    @validator('export_type')
    def validate_export_type(cls, v):
        allowed_types = ['csv', 'excel', 'json']
        if v not in allowed_types:
            raise ValueError(f'export_type must be one of: {", ".join(allowed_types)}')
        return v


class DataExportCreate(DataExportBase, UserMixin):
    """Schema for creating a data export."""
    pass


class DataExportUpdate(BaseSchema):
    """Schema for updating a data export."""
    status: Optional[str] = Field(None, max_length=50)
    total_records: Optional[int] = Field(None, ge=0)
    file_path: Optional[str] = Field(None, max_length=1000)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    download_count: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['pending', 'processing', 'completed', 'failed']
            if v not in allowed_statuses:
                raise ValueError(f'status must be one of: {", ".join(allowed_statuses)}')
        return v


class DataExportResponse(DataExportBase, TimestampMixin, UserMixin):
    """Schema for data export response."""
    id: UUID
    status: str = 'pending'
    total_records: int = 0
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_count: int = 0
    error_message: Optional[str] = None


class DataExportListResponse(BaseSchema):
    """Schema for data export list response."""
    exports: List[DataExportResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# API Request/Response Schemas
# ============================================================================

# Search and Filtering Schemas
class SearchFilters(BaseSchema):
    """Schema for search filters."""
    query: Optional[str] = None
    industry: Optional[List[str]] = None
    company_size: Optional[List[str]] = None
    location: Optional[LocationSchema] = None
    technology_stack: Optional[List[str]] = None
    revenue_range: Optional[List[str]] = None
    employee_count_min: Optional[int] = Field(None, ge=0)
    employee_count_max: Optional[int] = Field(None, ge=0)
    lead_score_min: Optional[Decimal] = Field(None, ge=0)
    lead_score_max: Optional[Decimal] = Field(None, ge=0)
    data_quality_score_min: Optional[Decimal] = Field(None, ge=0, le=1)
    data_quality_score_max: Optional[Decimal] = Field(None, ge=0, le=1)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class PaginationParams(BaseSchema):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class SortParams(BaseSchema):
    """Schema for sorting parameters."""
    sort_by: str = Field(default='created_at')
    sort_order: str = Field(default='desc')

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be either "asc" or "desc"')
        return v


# Search Request Schema
class SearchRequest(BaseSchema):
    """Schema for search requests."""
    filters: Optional[SearchFilters] = None
    pagination: Optional[PaginationParams] = PaginationParams()
    sort: Optional[SortParams] = SortParams()


# Lead Scoring Schemas
class LeadScoreBreakdown(BaseSchema):
    """Schema for lead score breakdown."""
    contact_completeness: Decimal = Field(ge=0)
    business_indicators: Decimal = Field(ge=0)
    data_quality: Decimal = Field(ge=0)
    engagement_potential: Decimal = Field(ge=0)
    total_score: Decimal = Field(ge=0)
    score_factors: Dict[str, Any] = Field(default_factory=dict)


class LeadResponse(BaseSchema):
    """Schema for lead response with enhanced data."""
    company: CompanyResponse
    contacts: List[ContactResponse]
    lead_score_breakdown: LeadScoreBreakdown
    insights: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class LeadListResponse(BaseSchema):
    """Schema for lead list response."""
    leads: List[LeadResponse]
    total: int
    page: int
    size: int
    pages: int
    summary: Dict[str, Any] = Field(default_factory=dict)


# Analytics Schemas
class AnalyticsTimeRange(BaseSchema):
    """Schema for analytics time range."""
    start_date: datetime
    end_date: datetime


class JobSummaryAnalytics(BaseSchema):
    """Schema for job summary analytics."""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    running_jobs: int = 0
    total_companies_found: int = 0
    total_contacts_found: int = 0
    average_completion_time: Optional[float] = None
    success_rate: Decimal = Field(ge=0, le=1)


class LeadQualityDistribution(BaseSchema):
    """Schema for lead quality distribution."""
    high_quality: int = 0  # score >= 80
    medium_quality: int = 0  # score 50-79
    low_quality: int = 0  # score < 50
    total_leads: int = 0
    average_score: Decimal = Field(ge=0)


class ContactDataInsights(BaseSchema):
    """Schema for contact data insights."""
    total_contacts: int = 0
    verified_contacts: int = 0
    decision_makers: int = 0
    contacts_with_email: int = 0
    contacts_with_phone: int = 0
    contacts_with_linkedin: int = 0
    average_experience_years: Optional[float] = None
    top_job_titles: List[Dict[str, Union[str, int]]] = Field(default_factory=list)
    seniority_distribution: Dict[str, int] = Field(default_factory=dict)


class IndustryBreakdown(BaseSchema):
    """Schema for industry breakdown."""
    industry_distribution: Dict[str, int] = Field(default_factory=dict)
    top_industries: List[Dict[str, Union[str, int]]] = Field(default_factory=list)
    company_size_distribution: Dict[str, int] = Field(default_factory=dict)
    revenue_distribution: Dict[str, int] = Field(default_factory=dict)


class TechnologyTrends(BaseSchema):
    """Schema for technology trends."""
    top_technologies: List[Dict[str, Union[str, int]]] = Field(default_factory=list)
    technology_adoption_rate: Dict[str, Decimal] = Field(default_factory=dict)
    emerging_technologies: List[str] = Field(default_factory=list)
    technology_combinations: List[Dict[str, Any]] = Field(default_factory=list)


class AnalyticsResponse(BaseSchema):
    """Schema for comprehensive analytics response."""
    time_range: AnalyticsTimeRange
    job_summary: JobSummaryAnalytics
    lead_quality: LeadQualityDistribution
    contact_insights: ContactDataInsights
    industry_breakdown: IndustryBreakdown
    technology_trends: TechnologyTrends
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# WebSocket Schemas
class WebSocketMessage(BaseSchema):
    """Schema for WebSocket messages."""
    type: str = Field(..., max_length=50)
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobProgressUpdate(BaseSchema):
    """Schema for job progress updates via WebSocket."""
    job_id: UUID
    status: str
    progress_percentage: Decimal
    processed_targets: int
    total_targets: int
    companies_found: int
    contacts_found: int
    estimated_completion: Optional[datetime] = None
    message: Optional[str] = None


class LeadDiscoveryNotification(BaseSchema):
    """Schema for lead discovery notifications."""
    job_id: UUID
    company_id: UUID
    company_name: str
    lead_score: Decimal
    contacts_found: int
    key_insights: List[str] = Field(default_factory=list)


# Error Schemas
class ErrorDetail(BaseSchema):
    """Schema for error details."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseSchema):
    """Schema for error responses."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Success Schemas
class SuccessResponse(BaseSchema):
    """Schema for success responses."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Health Check Schema
class HealthCheckResponse(BaseSchema):
    """Schema for health check response."""
    status: str = 'healthy'
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    database: str = 'connected'
    redis: str = 'connected'
    services: Dict[str, str] = Field(default_factory=dict)
    uptime: float = 0.0