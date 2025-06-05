"""Services package for business logic and data access."""

from .supabase_service import (
    SupabaseService,
    CompanyService,
    ContactService,
    ScrapingJobService,
    ScrapedDataService,
    DataExportService,
    UserActivityService,
    SystemMetricsService,
    APIKeyService,
    DatabaseError,
    NotFoundError,
    ValidationError
)

from .service_factory import (
    ServiceFactory,
    get_service_factory,
    get_company_service,
    get_contact_service,
    get_scraping_job_service,
    get_scraped_data_service,
    get_data_export_service,
    get_user_activity_service,
    get_system_metrics_service,
    get_api_key_service
)

from .database_utils import (
    DatabaseUtils,
    get_database_utils
)

__all__ = [
    # Base service classes
    "SupabaseService",
    "CompanyService",
    "ContactService",
    "ScrapingJobService",
    "ScrapedDataService",
    "DataExportService",
    "UserActivityService",
    "SystemMetricsService",
    "APIKeyService",
    
    # Exceptions
    "DatabaseError",
    "NotFoundError",
    "ValidationError",
    
    # Service factory
    "ServiceFactory",
    "get_service_factory",
    "get_company_service",
    "get_contact_service",
    "get_scraping_job_service",
    "get_scraped_data_service",
    "get_data_export_service",
    "get_user_activity_service",
    "get_system_metrics_service",
    "get_api_key_service",
    
    # Database utilities
    "DatabaseUtils",
    "get_database_utils"
]