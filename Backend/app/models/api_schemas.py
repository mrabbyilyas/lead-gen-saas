from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator

from .schemas import BaseSchema, LocationSchema, PaginationParams, SortParams


# ============================================================================
# Scraping API Schemas
# ============================================================================

class ScrapingSearchParameters(BaseSchema):
    """Schema for scraping search parameters."""
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    location: Optional[LocationSchema] = None
    industry: Optional[List[str]] = None
    company_size: Optional[List[str]] = None
    max_results: int = Field(default=100, ge=1, le=1000)
    include_contacts: bool = Field(default=True)
    contact_roles: Optional[List[str]] = None  # e.g., ['CEO', 'CTO', 'Marketing Manager']
    exclude_domains: Optional[List[str]] = None
    min_employee_count: Optional[int] = Field(None, ge=1)
    max_employee_count: Optional[int] = Field(None, ge=1)
    founded_after: Optional[int] = Field(None, ge=1800, le=2030)
    revenue_range: Optional[List[str]] = None
    technology_stack: Optional[List[str]] = None
    
    @validator('contact_roles')
    def validate_contact_roles(cls, v):
        if v:
            allowed_roles = [
                'CEO', 'CTO', 'CFO', 'COO', 'CMO', 'VP', 'Director', 'Manager',
                'Head of', 'Lead', 'Senior', 'Principal', 'Founder', 'Owner'
            ]
            for role in v:
                if not any(allowed_role.lower() in role.lower() for allowed_role in allowed_roles):
                    continue  # Allow custom roles
        return v


class ScrapingJobRequest(BaseSchema):
    """Schema for creating a scraping job."""
    job_name: str = Field(..., min_length=1, max_length=255)
    job_type: str = Field(...)
    search_parameters: ScrapingSearchParameters
    priority: str = Field(default='normal')
    schedule_at: Optional[datetime] = None
    webhook_url: Optional[HttpUrl] = None
    notification_email: Optional[str] = None
    
    @validator('job_type')
    def validate_job_type(cls, v):
        allowed_types = ['google_my_business', 'linkedin', 'website', 'directory', 'multi_source']
        if v not in allowed_types:
            raise ValueError(f'job_type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'normal', 'high', 'urgent']
        if v not in allowed_priorities:
            raise ValueError(f'priority must be one of: {", ".join(allowed_priorities)}')
        return v


class ScrapingJobStatusResponse(BaseSchema):
    """Schema for scraping job status response."""
    job_id: UUID
    job_name: str
    status: str
    progress_percentage: Decimal
    total_targets: int
    processed_targets: int
    successful_extractions: int
    failed_extractions: int
    companies_found: int
    contacts_found: int
    start_time: Optional[datetime]
    estimated_completion: Optional[datetime]
    elapsed_time: Optional[float]  # in seconds
    remaining_time: Optional[float]  # in seconds
    current_operation: Optional[str]
    error_message: Optional[str]
    performance_metrics: Optional[Dict[str, Any]]
    created_at: datetime


class ScrapingJobListRequest(BaseSchema):
    """Schema for listing scraping jobs with filters."""
    status: Optional[List[str]] = None
    job_type: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    pagination: PaginationParams = PaginationParams()
    sort: SortParams = SortParams(sort_by='created_at', sort_order='desc')


# ============================================================================
# Lead Search and Filtering API Schemas
# ============================================================================

class LeadSearchFilters(BaseSchema):
    """Schema for advanced lead search filters."""
    # Company filters
    company_name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[List[str]] = None
    company_size: Optional[List[str]] = None
    location: Optional[LocationSchema] = None
    technology_stack: Optional[List[str]] = None
    revenue_range: Optional[List[str]] = None
    employee_count_min: Optional[int] = Field(None, ge=0)
    employee_count_max: Optional[int] = Field(None, ge=0)
    founded_after: Optional[int] = Field(None, ge=1800, le=2030)
    founded_before: Optional[int] = Field(None, ge=1800, le=2030)
    
    # Contact filters
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[List[str]] = None
    seniority_level: Optional[List[str]] = None
    has_email: Optional[bool] = None
    has_phone: Optional[bool] = None
    has_linkedin: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    # Scoring filters
    lead_score_min: Optional[Decimal] = Field(None, ge=0)
    lead_score_max: Optional[Decimal] = Field(None, ge=0)
    data_quality_score_min: Optional[Decimal] = Field(None, ge=0, le=1)
    data_quality_score_max: Optional[Decimal] = Field(None, ge=0, le=1)
    contact_quality_score_min: Optional[Decimal] = Field(None, ge=0, le=1)
    contact_quality_score_max: Optional[Decimal] = Field(None, ge=0, le=1)
    engagement_potential_min: Optional[Decimal] = Field(None, ge=0, le=1)
    engagement_potential_max: Optional[Decimal] = Field(None, ge=0, le=1)
    
    # Growth signals
    has_growth_signals: Optional[bool] = None
    growth_signal_types: Optional[List[str]] = None  # ['hiring', 'funding', 'expansion']
    
    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    last_activity_after: Optional[datetime] = None
    last_activity_before: Optional[datetime] = None


class LeadSearchRequest(BaseSchema):
    """Schema for lead search requests."""
    filters: Optional[LeadSearchFilters] = None
    pagination: PaginationParams = PaginationParams()
    sort: SortParams = SortParams(sort_by='lead_score', sort_order='desc')
    include_contacts: bool = Field(default=True)
    include_score_breakdown: bool = Field(default=False)
    include_insights: bool = Field(default=False)


class LeadEnrichmentRequest(BaseSchema):
    """Schema for lead enrichment requests."""
    company_ids: Optional[List[UUID]] = None
    contact_ids: Optional[List[UUID]] = None
    enrichment_types: List[str] = Field(..., min_items=1)
    priority: str = Field(default='normal')
    
    @validator('enrichment_types')
    def validate_enrichment_types(cls, v):
        allowed_types = [
            'contact_info', 'social_media', 'company_details', 'technology_stack',
            'growth_signals', 'competitive_analysis', 'pain_points', 'funding_info'
        ]
        for enrichment_type in v:
            if enrichment_type not in allowed_types:
                raise ValueError(f'enrichment_type must be one of: {", ".join(allowed_types)}')
        return v


# ============================================================================
# Analytics API Schemas
# ============================================================================

class AnalyticsRequest(BaseSchema):
    """Schema for analytics requests."""
    start_date: datetime
    end_date: datetime
    metrics: List[str] = Field(..., min_items=1)
    group_by: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    
    @validator('metrics')
    def validate_metrics(cls, v):
        allowed_metrics = [
            'job_summary', 'lead_quality', 'contact_insights', 'industry_breakdown',
            'technology_trends', 'conversion_rates', 'data_quality', 'performance'
        ]
        for metric in v:
            if metric not in allowed_metrics:
                raise ValueError(f'metric must be one of: {", ".join(allowed_metrics)}')
        return v
    
    @validator('group_by')
    def validate_group_by(cls, v):
        if v:
            allowed_groups = ['day', 'week', 'month', 'industry', 'company_size', 'job_type']
            for group in v:
                if group not in allowed_groups:
                    raise ValueError(f'group_by must be one of: {", ".join(allowed_groups)}')
        return v


class PerformanceMetrics(BaseSchema):
    """Schema for performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    p95_response_time: float = 0.0
    error_rate: Decimal = Field(ge=0, le=1)
    throughput: float = 0.0  # requests per second
    uptime_percentage: Decimal = Field(ge=0, le=1)


class ConversionRates(BaseSchema):
    """Schema for conversion rate metrics."""
    scraping_to_leads: Decimal = Field(ge=0, le=1)
    leads_to_qualified: Decimal = Field(ge=0, le=1)
    qualified_to_contacted: Decimal = Field(ge=0, le=1)
    contacted_to_responded: Decimal = Field(ge=0, le=1)
    total_conversion_rate: Decimal = Field(ge=0, le=1)


# ============================================================================
# Export API Schemas
# ============================================================================

class ExportRequest(BaseSchema):
    """Schema for data export requests."""
    export_name: str = Field(..., min_length=1, max_length=255)
    export_type: str = Field(...)
    data_type: str = Field(...)
    filters: Optional[Dict[str, Any]] = None
    fields: Optional[List[str]] = None  # Specific fields to export
    format_options: Optional[Dict[str, Any]] = None
    include_headers: bool = Field(default=True)
    max_records: Optional[int] = Field(None, ge=1, le=100000)
    notification_email: Optional[str] = None
    
    @validator('export_type')
    def validate_export_type(cls, v):
        allowed_types = ['csv', 'excel', 'json', 'pdf']
        if v not in allowed_types:
            raise ValueError(f'export_type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('data_type')
    def validate_data_type(cls, v):
        allowed_types = ['companies', 'contacts', 'leads', 'scraping_jobs', 'analytics']
        if v not in allowed_types:
            raise ValueError(f'data_type must be one of: {", ".join(allowed_types)}')
        return v


class ExportStatusResponse(BaseSchema):
    """Schema for export status response."""
    export_id: UUID
    export_name: str
    status: str
    progress_percentage: Decimal = Field(ge=0, le=100)
    total_records: int = 0
    processed_records: int = 0
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    estimated_completion: Optional[datetime] = None


# ============================================================================
# Webhook and Integration Schemas
# ============================================================================

class WebhookEvent(BaseSchema):
    """Schema for webhook events."""
    event_type: str = Field(..., max_length=50)
    event_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default='lead-gen-saas')
    version: str = Field(default='1.0')


class CRMIntegrationRequest(BaseSchema):
    """Schema for CRM integration requests."""
    crm_type: str = Field(...)
    api_credentials: Dict[str, str] = Field(...)
    sync_options: Dict[str, Any] = Field(default_factory=dict)
    field_mapping: Dict[str, str] = Field(default_factory=dict)
    
    @validator('crm_type')
    def validate_crm_type(cls, v):
        allowed_types = ['salesforce', 'hubspot', 'pipedrive', 'zoho', 'custom']
        if v not in allowed_types:
            raise ValueError(f'crm_type must be one of: {", ".join(allowed_types)}')
        return v


# ============================================================================
# Batch Operation Schemas
# ============================================================================

class BatchOperation(BaseSchema):
    """Schema for batch operations."""
    operation_type: str = Field(...)
    target_ids: List[UUID] = Field(..., min_items=1, max_items=1000)
    parameters: Optional[Dict[str, Any]] = None
    
    @validator('operation_type')
    def validate_operation_type(cls, v):
        allowed_operations = [
            'update_scores', 'enrich_data', 'validate_contacts', 'merge_duplicates',
            'export_data', 'delete_records', 'update_status'
        ]
        if v not in allowed_operations:
            raise ValueError(f'operation_type must be one of: {", ".join(allowed_operations)}')
        return v


class BatchOperationResponse(BaseSchema):
    """Schema for batch operation responses."""
    operation_id: UUID
    operation_type: str
    status: str
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    progress_percentage: Decimal = Field(ge=0, le=100)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# System and Monitoring Schemas
# ============================================================================

class SystemStatus(BaseSchema):
    """Schema for system status."""
    status: str = Field(default='operational')
    services: Dict[str, str] = Field(default_factory=dict)
    database_status: str = 'connected'
    redis_status: str = 'connected'
    celery_status: str = 'running'
    active_jobs: int = 0
    queue_size: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    disk_usage: float = 0.0
    uptime: float = 0.0
    last_check: datetime = Field(default_factory=datetime.utcnow)


class AlertConfiguration(BaseSchema):
    """Schema for alert configuration."""
    alert_type: str = Field(...)
    threshold: float = Field(...)
    comparison: str = Field(...)  # 'gt', 'lt', 'eq', 'gte', 'lte'
    notification_channels: List[str] = Field(..., min_items=1)
    is_enabled: bool = Field(default=True)
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed_types = [
            'error_rate', 'response_time', 'queue_size', 'memory_usage',
            'cpu_usage', 'disk_usage', 'failed_jobs', 'data_quality'
        ]
        if v not in allowed_types:
            raise ValueError(f'alert_type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('comparison')
    def validate_comparison(cls, v):
        allowed_comparisons = ['gt', 'lt', 'eq', 'gte', 'lte']
        if v not in allowed_comparisons:
            raise ValueError(f'comparison must be one of: {", ".join(allowed_comparisons)}')
        return v


# ============================================================================
# API Response Wrappers
# ============================================================================

class APIResponse(BaseSchema):
    """Generic API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    execution_time: Optional[float] = None  # in seconds


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    items: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class BulkResponse(BaseSchema):
    """Bulk operation response wrapper."""
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: float = 0.0
    items: List[Any] = Field(default_factory=list)