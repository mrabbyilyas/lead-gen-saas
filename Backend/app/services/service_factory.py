"""Service factory for dependency injection and service management."""

from typing import Dict, Type, TypeVar, Optional
from functools import lru_cache

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
)

T = TypeVar("T", bound=SupabaseService)


class ServiceFactory:
    """Factory class for creating and managing service instances."""

    def __init__(self) -> None:
        self._services: Dict[Type[SupabaseService], SupabaseService] = {}
        self._service_registry = {
            "company": CompanyService,
            "contact": ContactService,
            "scraping_job": ScrapingJobService,
            "scraped_data": ScrapedDataService,
            "data_export": DataExportService,
            "user_activity": UserActivityService,
            "system_metrics": SystemMetricsService,
            "api_key": APIKeyService,
        }
        self._service_table_mapping = {
            CompanyService: "companies",
            ContactService: "contacts",
            ScrapingJobService: "scraping_jobs",
            ScrapedDataService: "scraped_data",
            DataExportService: "data_exports",
            UserActivityService: "user_activities",
            SystemMetricsService: "system_metrics",
            APIKeyService: "api_keys",
        }

    def get_service(self, service_class: Type[T]) -> T:
        """Get or create a service instance."""
        if service_class not in self._services:
            # Get table name from service class mapping
            table_name = self._get_table_name_for_service(service_class)
            self._services[service_class] = service_class(table_name)
        return self._services[service_class]  # type: ignore

    def _get_table_name_for_service(self, service_class: Type[SupabaseService]) -> str:
        """Get the table name for a service class."""
        if service_class in self._service_table_mapping:
            return self._service_table_mapping[service_class]
        raise ValueError(f"Unknown service class: {service_class}")

    def get_service_by_name(self, service_name: str) -> Optional[SupabaseService]:
        """Get a service by name."""
        if service_name in self._service_registry:
            service_class = self._service_registry[service_name]
            return self.get_service(service_class)
        return None

    def clear_cache(self) -> None:
        """Clear all cached service instances."""
        self._services.clear()

    @property
    def company_service(self) -> CompanyService:
        """Get company service instance."""
        return self.get_service(CompanyService)

    @property
    def contact_service(self) -> ContactService:
        """Get contact service instance."""
        return self.get_service(ContactService)

    @property
    def scraping_job_service(self) -> ScrapingJobService:
        """Get scraping job service instance."""
        return self.get_service(ScrapingJobService)

    @property
    def scraped_data_service(self) -> ScrapedDataService:
        """Get scraped data service instance."""
        return self.get_service(ScrapedDataService)

    @property
    def data_export_service(self) -> DataExportService:
        """Get data export service instance."""
        return self.get_service(DataExportService)

    @property
    def user_activity_service(self) -> UserActivityService:
        """Get user activity service instance."""
        return self.get_service(UserActivityService)

    @property
    def system_metrics_service(self) -> SystemMetricsService:
        """Get system metrics service instance."""
        return self.get_service(SystemMetricsService)

    @property
    def api_key_service(self) -> APIKeyService:
        """Get API key service instance."""
        return self.get_service(APIKeyService)


# Global service factory instance
@lru_cache(maxsize=1)
def get_service_factory() -> ServiceFactory:
    """Get the global service factory instance."""
    return ServiceFactory()


# Convenience functions for getting services
def get_company_service() -> CompanyService:
    """Get company service instance."""
    return get_service_factory().company_service


def get_contact_service() -> ContactService:
    """Get contact service instance."""
    return get_service_factory().contact_service


def get_scraping_job_service() -> ScrapingJobService:
    """Get scraping job service instance."""
    return get_service_factory().scraping_job_service


def get_scraped_data_service() -> ScrapedDataService:
    """Get scraped data service instance."""
    return get_service_factory().scraped_data_service


def get_data_export_service() -> DataExportService:
    """Get data export service instance."""
    return get_service_factory().data_export_service


def get_user_activity_service() -> UserActivityService:
    """Get user activity service instance."""
    return get_service_factory().user_activity_service


def get_system_metrics_service() -> SystemMetricsService:
    """Get system metrics service instance."""
    return get_service_factory().system_metrics_service


def get_api_key_service() -> APIKeyService:
    """Get API key service instance."""
    return get_service_factory().api_key_service
