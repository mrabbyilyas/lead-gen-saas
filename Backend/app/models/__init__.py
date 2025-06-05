"""Models package for Lead Generation SaaS.

This package contains:
- SQLAlchemy database models (database.py)
- Pydantic schemas for data validation (schemas.py)
- API-specific schemas for request/response handling (api_schemas.py)
"""

# Database Models
from .database import (
    Base,
    Company,
    Contact,
    ScrapingJob,
    ScrapedData,
    DataExport,
    UserActivity,
    SystemMetrics,
    APIKey,
)

# Core Pydantic Schemas
from .schemas import (
    # Base schemas
    BaseSchema,
    TimestampMixin,
    UserMixin,
    LocationSchema,
    # Company schemas
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    # Contact schemas
    ContactBase,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse,
    # Scraping Job schemas
    ScrapingJobBase,
    ScrapingJobCreate,
    ScrapingJobUpdate,
    ScrapingJobResponse,
    ScrapingJobListResponse,
    # Scraped Data schemas
    ScrapedDataBase,
    ScrapedDataCreate,
    ScrapedDataUpdate,
    ScrapedDataResponse,
    ScrapedDataListResponse,
    # Data Export schemas
    DataExportBase,
    DataExportCreate,
    DataExportUpdate,
    DataExportResponse,
    DataExportListResponse,
    # Search and filtering
    SearchFilters,
    PaginationParams,
    SortParams,
    SearchRequest,
    # Lead scoring and analytics
    LeadScoreBreakdown,
    LeadResponse,
    LeadListResponse,
    AnalyticsTimeRange,
    JobSummaryAnalytics,
    LeadQualityDistribution,
    ContactDataInsights,
    IndustryBreakdown,
    TechnologyTrends,
    AnalyticsResponse,
    # WebSocket schemas
    WebSocketMessage,
    JobProgressUpdate,
    LeadDiscoveryNotification,
    # Response schemas
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    HealthCheckResponse,
)

# API-specific schemas
from .api_schemas import (
    # Scraping API
    ScrapingSearchParameters,
    ScrapingJobRequest,
    ScrapingJobStatusResponse,
    ScrapingJobListRequest,
    # Lead search and filtering
    LeadSearchFilters,
    LeadSearchRequest,
    LeadEnrichmentRequest,
    # Analytics API
    AnalyticsRequest,
    PerformanceMetrics,
    ConversionRates,
    # Export API
    ExportRequest,
    ExportStatusResponse,
    # Webhooks and integrations
    WebhookEvent,
    CRMIntegrationRequest,
    # Batch operations
    BatchOperation,
    BatchOperationResponse,
    # System monitoring
    SystemStatus,
    AlertConfiguration,
    # API response wrappers
    APIResponse,
    PaginatedResponse,
    BulkResponse,
)

__all__ = [
    # Database Models
    "Base",
    "Company",
    "Contact",
    "ScrapingJob",
    "ScrapedData",
    "DataExport",
    "UserActivity",
    "SystemMetrics",
    "APIKey",
    # Base schemas
    "BaseSchema",
    "TimestampMixin",
    "UserMixin",
    "LocationSchema",
    # Company schemas
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyListResponse",
    # Contact schemas
    "ContactBase",
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    "ContactListResponse",
    # Scraping Job schemas
    "ScrapingJobBase",
    "ScrapingJobCreate",
    "ScrapingJobUpdate",
    "ScrapingJobResponse",
    "ScrapingJobListResponse",
    # Scraped Data schemas
    "ScrapedDataBase",
    "ScrapedDataCreate",
    "ScrapedDataUpdate",
    "ScrapedDataResponse",
    "ScrapedDataListResponse",
    # Data Export schemas
    "DataExportBase",
    "DataExportCreate",
    "DataExportUpdate",
    "DataExportResponse",
    "DataExportListResponse",
    # Search and filtering
    "SearchFilters",
    "PaginationParams",
    "SortParams",
    "SearchRequest",
    # Lead scoring and analytics
    "LeadScoreBreakdown",
    "LeadResponse",
    "LeadListResponse",
    "AnalyticsTimeRange",
    "JobSummaryAnalytics",
    "LeadQualityDistribution",
    "ContactDataInsights",
    "IndustryBreakdown",
    "TechnologyTrends",
    "AnalyticsResponse",
    # WebSocket schemas
    "WebSocketMessage",
    "JobProgressUpdate",
    "LeadDiscoveryNotification",
    # Response schemas
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
    # API-specific schemas
    "ScrapingSearchParameters",
    "ScrapingJobRequest",
    "ScrapingJobStatusResponse",
    "ScrapingJobListRequest",
    "LeadSearchFilters",
    "LeadSearchRequest",
    "LeadEnrichmentRequest",
    "AnalyticsRequest",
    "PerformanceMetrics",
    "ConversionRates",
    "ExportRequest",
    "ExportStatusResponse",
    "WebhookEvent",
    "CRMIntegrationRequest",
    "BatchOperation",
    "BatchOperationResponse",
    "SystemStatus",
    "AlertConfiguration",
    "APIResponse",
    "PaginatedResponse",
    "BulkResponse",
]
