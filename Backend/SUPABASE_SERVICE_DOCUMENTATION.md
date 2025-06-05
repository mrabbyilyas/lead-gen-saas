# Supabase Service Layer Documentation

This document provides comprehensive documentation for the Supabase service layer implementation in the Lead Generation SaaS application.

## Overview

The Supabase service layer provides a clean abstraction over the Supabase database operations, offering:

- **Type-safe CRUD operations** for all entities
- **Consistent error handling** with custom exceptions
- **Advanced filtering and pagination** support
- **Bulk operations** for performance optimization
- **Database utilities** for maintenance and monitoring
- **Service factory pattern** for dependency injection

## Architecture

```
app/services/
├── __init__.py              # Package exports
├── supabase_service.py      # Core service classes
├── service_factory.py       # Dependency injection
└── database_utils.py        # Utility functions
```

## Core Components

### 1. Base Service Class

```python
from app.services import SupabaseService

class SupabaseService:
    """Base service class with common CRUD operations"""
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]
    def get_by_id(self, record_id: Union[str, UUID]) -> Optional[Dict[str, Any]]
    def get_all(self, filters=None, pagination=None, sort_params=None) -> Tuple[List[Dict], int]
    def update(self, record_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]
    def delete(self, record_id: Union[str, UUID]) -> bool
    def exists(self, record_id: Union[str, UUID]) -> bool
    def count(self, filters=None) -> int
```

### 2. Entity-Specific Services

#### CompanyService
```python
from app.services import get_company_service
from app.models.schemas import CompanyCreate, CompanyUpdate, PaginationParams

company_service = get_company_service()

# Create a company
company_data = CompanyCreate(
    name="TechCorp",
    domain="techcorp.com",
    industry="Technology"
)
company = company_service.create_company(company_data, user_id="user-123")

# Get companies with filtering
companies, total = company_service.get_companies_by_user(
    user_id="user-123",
    filters={"industry": "Technology"},
    pagination=PaginationParams(page=1, page_size=10)
)

# Search companies
results, total = company_service.search_companies(
    user_id="user-123",
    search_term="tech",
    pagination=PaginationParams(page=1, page_size=10)
)
```

#### ContactService
```python
from app.services import get_contact_service
from app.models.schemas import ContactCreate

contact_service = get_contact_service()

# Create a contact
contact_data = ContactCreate(
    company_id="company-uuid",
    first_name="John",
    last_name="Doe",
    email="john.doe@techcorp.com",
    job_title="Software Engineer"
)
contact = contact_service.create_contact(contact_data, user_id="user-123")

# Get contacts by company
contacts, total = contact_service.get_contacts_by_company(
    company_id="company-uuid",
    pagination=PaginationParams(page=1, page_size=20)
)
```

#### ScrapingJobService
```python
from app.services import get_scraping_job_service
from app.models.schemas import ScrapingJobCreate, ScrapingJobUpdate

job_service = get_scraping_job_service()

# Create a scraping job
job_data = ScrapingJobCreate(
    name="LinkedIn Company Scrape",
    target_url="https://linkedin.com/company/techcorp",
    scraping_config={"depth": 2, "rate_limit": 1.0}
)
job = job_service.create_job(job_data, user_id="user-123")

# Update job progress
progress_data = ScrapingJobUpdate(
    status="running",
    progress=45.5,
    processed_records=450,
    total_records=1000
)
updated_job = job_service.update_job_progress(job.id, progress_data.model_dump())

# Get active jobs
active_jobs = job_service.get_active_jobs(user_id="user-123")
```

### 3. Service Factory

```python
from app.services import get_service_factory, ServiceFactory

# Get the global service factory
factory = get_service_factory()

# Access services through factory
company_service = factory.company_service
contact_service = factory.contact_service

# Or use convenience functions
from app.services import (
    get_company_service,
    get_contact_service,
    get_scraping_job_service
)
```

### 4. Database Utilities

```python
from app.services import get_database_utils

db_utils = get_database_utils()

# Bulk operations
records = [
    {"name": "Company 1", "domain": "company1.com"},
    {"name": "Company 2", "domain": "company2.com"}
]
results = db_utils.bulk_insert("companies", records)

# Get table statistics
stats = db_utils.get_table_stats("companies", user_id="user-123")
print(f"Total companies: {stats['total_records']}")
print(f"Recent growth: {stats['growth_rate']}%")

# Database health check
health = db_utils.get_database_health()
print(f"Database status: {health['status']}")
print(f"Response time: {health['response_time_ms']}ms")

# Find duplicates
duplicates = db_utils.get_duplicate_records(
    "companies",
    duplicate_fields=["domain"],
    user_id="user-123"
)

# Clean up old records
deleted_count = db_utils.cleanup_old_records(
    "user_activities",
    days_old=90
)
```

## Advanced Features

### 1. Filtering

The service layer supports advanced filtering options:

```python
# Basic filters
filters = {
    "industry": "Technology",
    "size_range": "51-200"
}

# Range filters
filters = {
    "employee_count": {"gte": 50, "lte": 200},
    "founded_year": {"gt": 2000}
}

# Text search filters
filters = {
    "name": {"ilike": "tech"},  # Case-insensitive
    "description": {"like": "software"}  # Case-sensitive
}

# Array filters
filters = {
    "status": ["pending", "running"]  # IN clause
}
```

### 2. Pagination

```python
from app.models.schemas import PaginationParams

pagination = PaginationParams(
    page=2,
    page_size=25
)

results, total_count = service.get_all(
    filters=filters,
    pagination=pagination
)

# Calculate pagination info
total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
has_next = pagination.page < total_pages
has_prev = pagination.page > 1
```

### 3. Sorting

```python
from app.models.schemas import SortParams

sort_params = SortParams(
    sort_by="created_at",
    sort_order="desc"
)

results, total = service.get_all(
    sort_params=sort_params
)
```

### 4. Error Handling

```python
from app.services import DatabaseError, NotFoundError, ValidationError

try:
    company = company_service.get_company("invalid-id")
except NotFoundError:
    print("Company not found")
except ValidationError as e:
    print(f"Validation error: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
```

## Performance Optimization

### 1. Bulk Operations

```python
# Instead of multiple individual inserts
for record in records:
    service.create(record)  # Slow

# Use bulk insert
db_utils.bulk_insert("table_name", records)  # Fast
```

### 2. Efficient Queries

```python
# Use specific filters to reduce data transfer
filters = {
    "created_by": user_id,  # Always filter by user
    "status": "active"      # Add specific conditions
}

# Use pagination for large datasets
pagination = PaginationParams(page=1, page_size=50)
```

### 3. Connection Management

The service layer automatically manages Supabase connections through the singleton pattern:

```python
# Services reuse the same connection
company_service = get_company_service()  # Reuses connection
contact_service = get_contact_service()  # Reuses connection
```

## Testing

### Unit Testing Services

```python
import pytest
from unittest.mock import Mock, patch
from app.services import CompanyService
from app.models.schemas import CompanyCreate

@pytest.fixture
def mock_supabase_client():
    with patch('app.services.supabase_service.get_supabase_client') as mock:
        yield mock.return_value

def test_create_company(mock_supabase_client):
    # Setup mock
    mock_table = Mock()
    mock_supabase_client.table.return_value = mock_table
    mock_table.insert.return_value.execute.return_value.data = [{
        "id": "test-id",
        "name": "Test Company",
        "created_at": "2024-01-01T00:00:00Z"
    }]
    
    # Test
    service = CompanyService()
    company_data = CompanyCreate(name="Test Company")
    result = service.create_company(company_data, "user-123")
    
    # Assert
    assert result.name == "Test Company"
    mock_table.insert.assert_called_once()
```

### Integration Testing

```python
import pytest
from app.services import get_company_service
from app.models.schemas import CompanyCreate

@pytest.mark.integration
def test_company_crud_operations():
    service = get_company_service()
    
    # Create
    company_data = CompanyCreate(
        name="Integration Test Company",
        domain="test.com"
    )
    company = service.create_company(company_data, "test-user")
    assert company.id is not None
    
    # Read
    retrieved = service.get_company(company.id)
    assert retrieved.name == "Integration Test Company"
    
    # Update
    updated = service.update_company(
        company.id,
        CompanyUpdate(name="Updated Company")
    )
    assert updated.name == "Updated Company"
    
    # Delete
    deleted = service.delete(company.id)
    assert deleted is True
```

## Best Practices

### 1. Always Use User Filtering

```python
# Always filter by user_id for security
companies, total = company_service.get_companies_by_user(
    user_id=current_user.id,  # Security requirement
    filters=additional_filters
)
```

### 2. Handle Exceptions Gracefully

```python
try:
    result = service.create_company(company_data, user_id)
    return {"success": True, "data": result}
except ValidationError as e:
    return {"success": False, "error": "Invalid data", "details": str(e)}
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    return {"success": False, "error": "Internal server error"}
```

### 3. Use Pagination for Large Datasets

```python
# Always use pagination for user-facing endpoints
pagination = PaginationParams(
    page=request.page or 1,
    page_size=min(request.page_size or 20, 100)  # Limit max page size
)
```

### 4. Optimize Database Queries

```python
# Use specific field selection when possible
query = client.table("companies").select("id, name, domain")

# Use appropriate indexes for filtering
filters = {
    "created_by": user_id,     # Indexed field
    "industry": "Technology"   # Consider indexing frequently filtered fields
}
```

### 5. Monitor Performance

```python
# Use database utilities to monitor performance
stats = db_utils.get_table_stats("companies")
if stats["total_records"] > 100000:
    logger.warning(f"Large table detected: {stats}")

# Regular health checks
health = db_utils.get_database_health()
if health["status"] != "healthy":
    logger.error(f"Database health issue: {health}")
```

## Migration and Maintenance

### Database Cleanup

```python
# Clean up old user activities
deleted = db_utils.cleanup_old_records(
    "user_activities",
    days_old=90
)
logger.info(f"Cleaned up {deleted} old activity records")

# Archive old scraping jobs
old_job_ids = ["job1", "job2", "job3"]
result = db_utils.archive_records(
    "scraping_jobs",
    "scraping_jobs_archive",
    old_job_ids
)
logger.info(f"Archived {result['archived']} jobs")
```

### Performance Monitoring

```python
# Regular performance analysis
for table in ["companies", "contacts", "scraping_jobs"]:
    analysis = db_utils.optimize_table_performance(table)
    if analysis["suggestions"]:
        logger.info(f"Performance suggestions for {table}: {analysis['suggestions']}")
```

This service layer provides a robust, scalable foundation for all database operations in the Lead Generation SaaS application, with comprehensive error handling, performance optimization, and maintainability features.