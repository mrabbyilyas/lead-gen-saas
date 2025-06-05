"""Supabase service layer for database operations."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID
from datetime import datetime
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase_client
from app.models.schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    ContactCreate, ContactUpdate, ContactResponse,
    ScrapingJobCreate, ScrapingJobUpdate, ScrapingJobResponse,
    ScrapedDataCreate, ScrapedDataUpdate, ScrapedDataResponse,
    DataExportCreate, DataExportUpdate, DataExportResponse,
    UserActivityCreate, UserActivityResponse,
    SystemMetricsCreate, SystemMetricsResponse,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse,
    PaginationParams, SortParams
)

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class NotFoundError(DatabaseError):
    """Exception raised when a resource is not found."""
    pass


class ValidationError(DatabaseError):
    """Exception raised when validation fails."""
    pass


class SupabaseService:
    """Base service class for Supabase operations."""
    
    def __init__(self, table_name: str):
        self.client: Client = get_supabase_client()
        self.table_name = table_name
        self.table = self.client.table(table_name)
    
    def _handle_error(self, error: Exception, operation: str) -> None:
        """Handle and log database errors."""
        logger.error(f"Error in {operation} for table {self.table_name}: {str(error)}")
        if isinstance(error, APIError):
            if error.code == "PGRST116":  # Not found
                raise NotFoundError(f"Resource not found in {self.table_name}")
            elif "duplicate key" in str(error).lower():
                raise ValidationError(f"Duplicate entry in {self.table_name}")
        raise DatabaseError(f"Database operation failed: {str(error)}")
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to a query."""
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, list):
                    query = query.in_(key, value)
                elif isinstance(value, dict):
                    # Handle range filters
                    if "gte" in value:
                        query = query.gte(key, value["gte"])
                    if "lte" in value:
                        query = query.lte(key, value["lte"])
                    if "gt" in value:
                        query = query.gt(key, value["gt"])
                    if "lt" in value:
                        query = query.lt(key, value["lt"])
                    if "like" in value:
                        query = query.like(key, f"%{value['like']}%")
                    if "ilike" in value:
                        query = query.ilike(key, f"%{value['ilike']}%")
                else:
                    query = query.eq(key, value)
        return query
    
    def _apply_sorting(self, query, sort_params: Optional[SortParams]):
        """Apply sorting to a query."""
        if sort_params and sort_params.sort_by:
            if sort_params.sort_order == "desc":
                query = query.order(sort_params.sort_by, desc=True)
            else:
                query = query.order(sort_params.sort_by)
        return query
    
    def _apply_pagination(self, query, pagination: Optional[PaginationParams]):
        """Apply pagination to a query."""
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            query = query.range(offset, offset + pagination.page_size - 1)
        return query
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        try:
            # Add created_at timestamp
            data["created_at"] = datetime.utcnow().isoformat()
            data["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.table.insert(data).execute()
            if response.data:
                return response.data[0]
            raise DatabaseError("No data returned from insert operation")
        except Exception as e:
            self._handle_error(e, "create")
    
    def get_by_id(self, record_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        try:
            response = self.table.select("*").eq("id", str(record_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            self._handle_error(e, "get_by_id")
    
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        sort_params: Optional[SortParams] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get all records with optional filtering, pagination, and sorting."""
        try:
            # Build query
            query = self.table.select("*")
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Apply sorting
            query = self._apply_sorting(query, sort_params)
            
            # Get total count for pagination
            count_query = self.table.select("*", count="exact")
            if filters:
                count_query = self._apply_filters(count_query, filters)
            count_response = count_query.execute()
            total_count = count_response.count or 0
            
            # Apply pagination
            query = self._apply_pagination(query, pagination)
            
            response = query.execute()
            return response.data or [], total_count
        except Exception as e:
            self._handle_error(e, "get_all")
    
    def update(self, record_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by ID."""
        try:
            # Add updated_at timestamp
            data["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.table.update(data).eq("id", str(record_id)).execute()
            if response.data:
                return response.data[0]
            raise NotFoundError(f"Record with ID {record_id} not found")
        except Exception as e:
            self._handle_error(e, "update")
    
    def delete(self, record_id: Union[str, UUID]) -> bool:
        """Delete a record by ID."""
        try:
            response = self.table.delete().eq("id", str(record_id)).execute()
            return len(response.data) > 0
        except Exception as e:
            self._handle_error(e, "delete")
    
    def exists(self, record_id: Union[str, UUID]) -> bool:
        """Check if a record exists."""
        try:
            response = self.table.select("id").eq("id", str(record_id)).execute()
            return len(response.data) > 0
        except Exception as e:
            self._handle_error(e, "exists")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        try:
            query = self.table.select("*", count="exact")
            if filters:
                query = self._apply_filters(query, filters)
            response = query.execute()
            return response.count or 0
        except Exception as e:
            self._handle_error(e, "count")


class CompanyService(SupabaseService):
    """Service for company operations."""
    
    def __init__(self):
        super().__init__("companies")
    
    def create_company(self, company_data: CompanyCreate, user_id: str) -> CompanyResponse:
        """Create a new company."""
        data = company_data.model_dump(exclude_unset=True)
        data["created_by"] = user_id
        result = self.create(data)
        return CompanyResponse(**result)
    
    def get_company(self, company_id: Union[str, UUID]) -> Optional[CompanyResponse]:
        """Get a company by ID."""
        result = self.get_by_id(company_id)
        return CompanyResponse(**result) if result else None
    
    def update_company(self, company_id: Union[str, UUID], company_data: CompanyUpdate) -> Optional[CompanyResponse]:
        """Update a company."""
        data = company_data.model_dump(exclude_unset=True)
        result = self.update(company_id, data)
        return CompanyResponse(**result) if result else None
    
    def get_companies_by_user(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        sort_params: Optional[SortParams] = None
    ) -> Tuple[List[CompanyResponse], int]:
        """Get companies for a specific user."""
        user_filters = {"created_by": user_id}
        if filters:
            user_filters.update(filters)
        
        results, total = self.get_all(user_filters, pagination, sort_params)
        companies = [CompanyResponse(**result) for result in results]
        return companies, total
    
    def search_companies(
        self,
        user_id: str,
        search_term: str,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[CompanyResponse], int]:
        """Search companies by name or domain."""
        try:
            query = self.table.select("*").eq("created_by", user_id)
            
            # Apply search filters
            query = query.or_(f"name.ilike.%{search_term}%,domain.ilike.%{search_term}%")
            
            # Get total count
            count_query = self.table.select("*", count="exact").eq("created_by", user_id)
            count_query = count_query.or_(f"name.ilike.%{search_term}%,domain.ilike.%{search_term}%")
            count_response = count_query.execute()
            total_count = count_response.count or 0
            
            # Apply pagination
            query = self._apply_pagination(query, pagination)
            
            response = query.execute()
            companies = [CompanyResponse(**result) for result in response.data or []]
            return companies, total_count
        except Exception as e:
            self._handle_error(e, "search_companies")
    
    def get_companies_by_industry(
        self,
        user_id: str,
        industry: str,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[CompanyResponse], int]:
        """Get companies by industry."""
        filters = {"created_by": user_id, "industry": industry}
        results, total = self.get_all(filters, pagination)
        companies = [CompanyResponse(**result) for result in results]
        return companies, total


class ContactService(SupabaseService):
    """Service for contact operations."""
    
    def __init__(self):
        super().__init__("contacts")
    
    def create_contact(self, contact_data: ContactCreate, user_id: str) -> ContactResponse:
        """Create a new contact."""
        data = contact_data.model_dump(exclude_unset=True)
        data["created_by"] = user_id
        result = self.create(data)
        return ContactResponse(**result)
    
    def get_contact(self, contact_id: Union[str, UUID]) -> Optional[ContactResponse]:
        """Get a contact by ID."""
        result = self.get_by_id(contact_id)
        return ContactResponse(**result) if result else None
    
    def update_contact(self, contact_id: Union[str, UUID], contact_data: ContactUpdate) -> Optional[ContactResponse]:
        """Update a contact."""
        data = contact_data.model_dump(exclude_unset=True)
        result = self.update(contact_id, data)
        return ContactResponse(**result) if result else None
    
    def get_contacts_by_company(
        self,
        company_id: Union[str, UUID],
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[ContactResponse], int]:
        """Get contacts for a specific company."""
        filters = {"company_id": str(company_id)}
        results, total = self.get_all(filters, pagination)
        contacts = [ContactResponse(**result) for result in results]
        return contacts, total
    
    def get_contacts_by_user(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        sort_params: Optional[SortParams] = None
    ) -> Tuple[List[ContactResponse], int]:
        """Get contacts for a specific user."""
        user_filters = {"created_by": user_id}
        if filters:
            user_filters.update(filters)
        
        results, total = self.get_all(user_filters, pagination, sort_params)
        contacts = [ContactResponse(**result) for result in results]
        return contacts, total
    
    def search_contacts(
        self,
        user_id: str,
        search_term: str,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[ContactResponse], int]:
        """Search contacts by name or email."""
        try:
            query = self.table.select("*").eq("created_by", user_id)
            
            # Apply search filters
            query = query.or_(f"first_name.ilike.%{search_term}%,last_name.ilike.%{search_term}%,email.ilike.%{search_term}%")
            
            # Get total count
            count_query = self.table.select("*", count="exact").eq("created_by", user_id)
            count_query = count_query.or_(f"first_name.ilike.%{search_term}%,last_name.ilike.%{search_term}%,email.ilike.%{search_term}%")
            count_response = count_query.execute()
            total_count = count_response.count or 0
            
            # Apply pagination
            query = self._apply_pagination(query, pagination)
            
            response = query.execute()
            contacts = [ContactResponse(**result) for result in response.data or []]
            return contacts, total_count
        except Exception as e:
            self._handle_error(e, "search_contacts")


class ScrapingJobService(SupabaseService):
    """Service for scraping job operations."""
    
    def __init__(self):
        super().__init__("scraping_jobs")
    
    def create_job(self, job_data: ScrapingJobCreate, user_id: str) -> ScrapingJobResponse:
        """Create a new scraping job."""
        data = job_data.model_dump(exclude_unset=True)
        data["created_by"] = user_id
        result = self.create(data)
        return ScrapingJobResponse(**result)
    
    def get_job(self, job_id: Union[str, UUID]) -> Optional[ScrapingJobResponse]:
        """Get a scraping job by ID."""
        result = self.get_by_id(job_id)
        return ScrapingJobResponse(**result) if result else None
    
    def update_job(self, job_id: Union[str, UUID], job_data: ScrapingJobUpdate) -> Optional[ScrapingJobResponse]:
        """Update a scraping job."""
        data = job_data.model_dump(exclude_unset=True)
        result = self.update(job_id, data)
        return ScrapingJobResponse(**result) if result else None
    
    def get_jobs_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
        sort_params: Optional[SortParams] = None
    ) -> Tuple[List[ScrapingJobResponse], int]:
        """Get scraping jobs for a specific user."""
        filters = {"created_by": user_id}
        if status:
            filters["status"] = status
        
        results, total = self.get_all(filters, pagination, sort_params)
        jobs = [ScrapingJobResponse(**result) for result in results]
        return jobs, total
    
    def update_job_progress(self, job_id: Union[str, UUID], progress_data: Dict[str, Any]) -> Optional[ScrapingJobResponse]:
        """Update job progress and statistics."""
        return self.update_job(job_id, ScrapingJobUpdate(**progress_data))
    
    def get_active_jobs(self, user_id: str) -> List[ScrapingJobResponse]:
        """Get all active (running/pending) jobs for a user."""
        filters = {
            "created_by": user_id,
            "status": ["pending", "running"]
        }
        results, _ = self.get_all(filters)
        return [ScrapingJobResponse(**result) for result in results]


class ScrapedDataService(SupabaseService):
    """Service for scraped data operations."""
    
    def __init__(self):
        super().__init__("scraped_data")
    
    def create_scraped_data(self, data: ScrapedDataCreate) -> ScrapedDataResponse:
        """Create new scraped data."""
        data_dict = data.model_dump(exclude_unset=True)
        result = self.create(data_dict)
        return ScrapedDataResponse(**result)
    
    def get_scraped_data(self, data_id: Union[str, UUID]) -> Optional[ScrapedDataResponse]:
        """Get scraped data by ID."""
        result = self.get_by_id(data_id)
        return ScrapedDataResponse(**result) if result else None
    
    def update_scraped_data(self, data_id: Union[str, UUID], data: ScrapedDataUpdate) -> Optional[ScrapedDataResponse]:
        """Update scraped data."""
        data_dict = data.model_dump(exclude_unset=True)
        result = self.update(data_id, data_dict)
        return ScrapedDataResponse(**result) if result else None
    
    def get_data_by_job(
        self,
        job_id: Union[str, UUID],
        validation_status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[ScrapedDataResponse], int]:
        """Get scraped data for a specific job."""
        filters = {"job_id": str(job_id)}
        if validation_status:
            filters["validation_status"] = validation_status
        
        results, total = self.get_all(filters, pagination)
        data_list = [ScrapedDataResponse(**result) for result in results]
        return data_list, total
    
    def get_unprocessed_data(
        self,
        limit: Optional[int] = None
    ) -> List[ScrapedDataResponse]:
        """Get unprocessed scraped data."""
        filters = {"is_processed": False}
        pagination = PaginationParams(page=1, page_size=limit) if limit else None
        results, _ = self.get_all(filters, pagination)
        return [ScrapedDataResponse(**result) for result in results]


class DataExportService(SupabaseService):
    """Service for data export operations."""
    
    def __init__(self):
        super().__init__("data_exports")
    
    def create_export(self, export_data: DataExportCreate, user_id: str) -> DataExportResponse:
        """Create a new data export."""
        data = export_data.model_dump(exclude_unset=True)
        data["created_by"] = user_id
        result = self.create(data)
        return DataExportResponse(**result)
    
    def get_export(self, export_id: Union[str, UUID]) -> Optional[DataExportResponse]:
        """Get a data export by ID."""
        result = self.get_by_id(export_id)
        return DataExportResponse(**result) if result else None
    
    def update_export(self, export_id: Union[str, UUID], export_data: DataExportUpdate) -> Optional[DataExportResponse]:
        """Update a data export."""
        data = export_data.model_dump(exclude_unset=True)
        result = self.update(export_id, data)
        return DataExportResponse(**result) if result else None
    
    def get_exports_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[DataExportResponse], int]:
        """Get data exports for a specific user."""
        filters = {"created_by": user_id}
        if status:
            filters["status"] = status
        
        results, total = self.get_all(filters, pagination)
        exports = [DataExportResponse(**result) for result in results]
        return exports, total


class UserActivityService(SupabaseService):
    """Service for user activity tracking."""
    
    def __init__(self):
        super().__init__("user_activities")
    
    def log_activity(self, activity_data: UserActivityCreate) -> UserActivityResponse:
        """Log a user activity."""
        data = activity_data.model_dump(exclude_unset=True)
        result = self.create(data)
        return UserActivityResponse(**result)
    
    def get_user_activities(
        self,
        user_id: str,
        activity_type: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[UserActivityResponse], int]:
        """Get activities for a specific user."""
        filters = {"user_id": user_id}
        if activity_type:
            filters["activity_type"] = activity_type
        
        sort_params = SortParams(sort_by="created_at", sort_order="desc")
        results, total = self.get_all(filters, pagination, sort_params)
        activities = [UserActivityResponse(**result) for result in results]
        return activities, total


class SystemMetricsService(SupabaseService):
    """Service for system metrics."""
    
    def __init__(self):
        super().__init__("system_metrics")
    
    def record_metric(self, metric_data: SystemMetricsCreate) -> SystemMetricsResponse:
        """Record a system metric."""
        data = metric_data.model_dump(exclude_unset=True)
        result = self.create(data)
        return SystemMetricsResponse(**result)
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[SystemMetricsResponse], int]:
        """Get system metrics with optional filtering."""
        filters = {}
        if metric_name:
            filters["metric_name"] = metric_name
        if start_time:
            filters["recorded_at"] = {"gte": start_time.isoformat()}
        if end_time:
            if "recorded_at" not in filters:
                filters["recorded_at"] = {}
            filters["recorded_at"]["lte"] = end_time.isoformat()
        
        sort_params = SortParams(sort_by="recorded_at", sort_order="desc")
        results, total = self.get_all(filters, pagination, sort_params)
        metrics = [SystemMetricsResponse(**result) for result in results]
        return metrics, total


class APIKeyService(SupabaseService):
    """Service for API key management."""
    
    def __init__(self):
        super().__init__("api_keys")
    
    def create_api_key(self, key_data: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key."""
        data = key_data.model_dump(exclude_unset=True)
        result = self.create(data)
        return APIKeyResponse(**result)
    
    def get_api_key(self, key_id: Union[str, UUID]) -> Optional[APIKeyResponse]:
        """Get an API key by ID."""
        result = self.get_by_id(key_id)
        return APIKeyResponse(**result) if result else None
    
    def update_api_key(self, key_id: Union[str, UUID], key_data: APIKeyUpdate) -> Optional[APIKeyResponse]:
        """Update an API key."""
        data = key_data.model_dump(exclude_unset=True)
        result = self.update(key_id, data)
        return APIKeyResponse(**result) if result else None
    
    def get_keys_by_user(
        self,
        user_id: str,
        is_active: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[APIKeyResponse], int]:
        """Get API keys for a specific user."""
        filters = {"user_id": user_id}
        if is_active is not None:
            filters["is_active"] = is_active
        
        results, total = self.get_all(filters, pagination)
        keys = [APIKeyResponse(**result) for result in results]
        return keys, total
    
    def validate_api_key(self, key_hash: str) -> Optional[APIKeyResponse]:
        """Validate an API key by hash."""
        try:
            response = self.table.select("*").eq("key_hash", key_hash).eq("is_active", True).execute()
            if response.data:
                # Update last_used_at
                key_id = response.data[0]["id"]
                self.update(key_id, {"last_used_at": datetime.utcnow().isoformat()})
                return APIKeyResponse(**response.data[0])
            return None
        except Exception as e:
            self._handle_error(e, "validate_api_key")