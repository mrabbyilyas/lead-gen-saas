# Web Scraping Engine Documentation

## Overview

The Web Scraping Engine is a comprehensive, multi-source scraping system designed to extract company and contact information from various online sources. It provides a robust, scalable, and ethical approach to data collection with built-in rate limiting, proxy management, and error handling.

## Architecture

### Core Components

1. **Base Scraper** (`base_scraper.py`)
   - Abstract base class for all scrapers
   - Common functionality and interfaces
   - Error handling and validation

2. **Specific Scrapers**
   - **Google Scraper** (`google_scraper.py`) - Google My Business and Search
   - **LinkedIn Scraper** (`linkedin_scraper.py`) - LinkedIn companies and people
   - **Website Scraper** (`website_scraper.py`) - General website scraping

3. **Management Layer**
   - **Scraper Factory** (`scraper_factory.py`) - Creates and configures scrapers
   - **Scraper Manager** (`scraper_manager.py`) - Orchestrates scraping jobs
   - **Rate Limiter** (`rate_limiter.py`) - Controls request rates
   - **Proxy Manager** (`proxy_manager.py`) - Manages proxy rotation

## Features

### Multi-Source Support
- **Google My Business**: Extract business listings with ratings, addresses, phone numbers
- **LinkedIn**: Company profiles and employee information
- **General Websites**: Contact pages, about sections, team directories

### Rate Limiting
- Domain-specific rate limits
- Global rate limits
- Adaptive rate limiting based on response times
- Exponential backoff on failures

### Proxy Management
- Automatic proxy rotation
- Health checking for proxies
- Multiple rotation strategies (round-robin, random, domain-specific)
- Proxy performance tracking

### Error Handling
- Comprehensive error classification
- Automatic retries with exponential backoff
- Graceful degradation on failures
- Detailed error reporting

### Data Extraction
- Company information (name, domain, address, phone, industry)
- Contact information (name, email, phone, job title)
- Social media links
- Business descriptions and metadata

### Job Management
- Asynchronous job processing
- Job queuing and prioritization
- Progress tracking
- Batch processing support
- Job cancellation and cleanup

## Usage Examples

### Basic Scraping

```python
from app.services.scraper import auto_select_scraper, ScrapingConfig

# Create configuration
config = ScrapingConfig(
    max_pages=5,
    delay_between_requests=1.0,
    timeout=30,
    respect_robots_txt=True
)

# Auto-select best scraper for query
scraper = auto_select_scraper("restaurants in New York", config)

# Execute scraping
result = await scraper.scrape("restaurants in New York", location="New York, NY")

# Access results
print(f"Found {len(result.companies)} companies")
print(f"Found {len(result.contacts)} contacts")
for company in result.companies:
    print(f"Company: {company.name} - {company.website}")
```

### Using Scraper Manager

```python
from app.services.scraper import scraper_manager, ScraperType

# Create a scraping job
job_id = await scraper_manager.create_job(
    query="tech companies in San Francisco",
    scraper_type=ScraperType.GOOGLE,
    metadata={"location": "San Francisco, CA"}
)

# Check job status
job_info = await scraper_manager.get_job(job_id)
print(f"Job status: {job_info['status']}")
print(f"Progress: {job_info['progress']}%")

# Get results when completed
result = await scraper_manager.get_job_result(job_id)
if result:
    print(f"Scraping completed with {result.total_records_found} records")
```

### Batch Processing

```python
# Create multiple jobs
queries = [
    "restaurants in New York",
    "hotels in Los Angeles",
    "tech companies in Seattle"
]

job_ids = await scraper_manager.create_batch_job(
    queries=queries,
    scraper_type=ScraperType.AUTO
)

# Monitor all jobs
for job_id in job_ids:
    job_info = await scraper_manager.get_job(job_id)
    print(f"Job {job_id}: {job_info['status']}")
```

### LinkedIn Scraping with Login

```python
from app.services.scraper import LinkedInScraper

# Create LinkedIn scraper
scraper = LinkedInScraper(config)

# Set login credentials (optional but recommended)
scraper.set_login_credentials("your_email@example.com", "your_password")

# Scrape LinkedIn
result = await scraper.scrape("software engineers", location="San Francisco")
```

### Website Scraping

```python
from app.services.scraper import WebsiteScraper

# Create website scraper
scraper = WebsiteScraper(config)

# Scrape a specific website
result = await scraper.scrape("https://example-company.com")

# Results include company info and contacts found on the site
print(f"Company: {result.companies[0].name}")
print(f"Contacts found: {len(result.contacts)}")
```

## Configuration

### Scraping Configuration

```python
from app.services.scraper import ScrapingConfig

config = ScrapingConfig(
    max_pages=10,                    # Maximum pages to scrape
    delay_between_requests=2.0,      # Delay between requests (seconds)
    timeout=45,                      # Request timeout (seconds)
    max_retries=3,                   # Maximum retry attempts
    use_proxy=True,                  # Enable proxy usage
    respect_robots_txt=True,         # Respect robots.txt
    user_agent="Custom Bot 1.0"      # Custom user agent
)
```

### Rate Limiting

```python
from app.services.scraper import RateLimiter, AdaptiveRateLimiter

# Basic rate limiter
rate_limiter = RateLimiter(
    requests_per_minute=30,
    requests_per_hour=1000
)

# Adaptive rate limiter (adjusts based on response times)
adaptive_limiter = AdaptiveRateLimiter(
    requests_per_minute=30,
    requests_per_hour=1000
)

# Set in scraper factory
scraper_factory.set_rate_limiter(adaptive_limiter)
```

### Proxy Management

```python
from app.services.scraper import ProxyManager

# Create proxy manager
proxy_manager = ProxyManager(
    proxy_list=[
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "socks5://proxy3.example.com:1080"
    ],
    rotation_strategy="round_robin"  # or "random", "domain_specific"
)

# Set in scraper factory
scraper_factory.set_proxy_manager(proxy_manager)
```

## Data Models

### ScrapingResult

```python
class ScrapingResult:
    source: ScrapingSource          # Source of the data
    status: ScrapingStatus          # Scraping status
    companies: List[CompanyCreate]  # Found companies
    contacts: List[ContactCreate]   # Found contacts
    total_records_found: int        # Total records found
    total_pages_scraped: int        # Pages scraped
    execution_time: float           # Execution time in seconds
    errors: List[str]               # Error messages
    warnings: List[str]             # Warning messages
    raw_data: Dict                  # Raw scraped data
```

### CompanyCreate

```python
class CompanyCreate:
    name: str                       # Company name
    domain: str                     # Company domain
    website: str                    # Company website
    phone: str                      # Phone number
    address: str                    # Physical address
    industry: str                   # Industry/category
    description: str                # Company description
    linkedin_url: str               # LinkedIn profile URL
    source: str                     # Data source
    source_url: str                 # Source URL
```

### ContactCreate

```python
class ContactCreate:
    first_name: str                 # First name
    last_name: str                  # Last name
    email: str                      # Email address
    phone: str                      # Phone number
    job_title: str                  # Job title
    company: str                    # Company name
    linkedin_url: str               # LinkedIn profile URL
    source: str                     # Data source
```

## Error Handling

### Error Types

- **ScrapingError**: General scraping errors
- **RateLimitError**: Rate limit exceeded
- **BlockedError**: Access blocked by target site
- **TimeoutError**: Request timeout
- **ValidationError**: Invalid input data

### Error Recovery

```python
try:
    result = await scraper.scrape(query)
except RateLimitError:
    # Wait and retry
    await asyncio.sleep(60)
    result = await scraper.scrape(query)
except BlockedError:
    # Switch to different scraper or proxy
    scraper = create_scraper(ScraperType.WEBSITE)
    result = await scraper.scrape(query)
except ScrapingError as e:
    # Log error and continue
    logger.error(f"Scraping failed: {e}")
```

## Best Practices

### Ethical Scraping

1. **Respect robots.txt**: Always check and respect robots.txt files
2. **Rate limiting**: Implement appropriate delays between requests
3. **User agent**: Use descriptive and honest user agent strings
4. **Terms of service**: Respect website terms of service
5. **Data usage**: Use scraped data responsibly and legally

### Performance Optimization

1. **Concurrent scraping**: Use async/await for concurrent operations
2. **Caching**: Cache results to avoid duplicate requests
3. **Selective scraping**: Only scrape necessary pages
4. **Proxy rotation**: Use proxies to distribute load
5. **Error handling**: Implement robust error handling and retries

### Security Considerations

1. **Credential management**: Store credentials securely
2. **Proxy security**: Use trusted proxy services
3. **Data encryption**: Encrypt sensitive scraped data
4. **Access control**: Limit access to scraping functionality
5. **Audit logging**: Log all scraping activities

## Monitoring and Debugging

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Scraper logs include:
# - Request URLs and responses
# - Rate limiting events
# - Proxy usage and failures
# - Data extraction results
# - Error details
```

### Metrics

```python
# Get scraper statistics
stats = await scraper_manager.get_job_stats()
print(f"Total jobs: {stats['total_jobs']}")
print(f"Active jobs: {stats['active_jobs']}")
print(f"Success rate: {stats['status_counts']['completed'] / stats['total_jobs']}")
```

## Integration with Supabase

The scraping engine integrates seamlessly with the Supabase service layer:

```python
from app.services.supabase_service import ServiceFactory
from app.services.scraper import scraper_manager

# Get services
company_service = ServiceFactory.get_company_service()
contact_service = ServiceFactory.get_contact_service()

# Create scraping job
job_id = await scraper_manager.create_job("tech companies in NYC")

# Wait for completion and save results
result = await scraper_manager.get_job_result(job_id)
if result and result.status == ScrapingStatus.COMPLETED:
    # Save companies
    for company_data in result.companies:
        company = await company_service.create(company_data)
        
        # Save associated contacts
        for contact_data in result.contacts:
            contact_data.company_id = company.id
            await contact_service.create(contact_data)
```

## API Integration

The scraping engine can be exposed through REST API endpoints:

```python
# In your FastAPI router
from app.services.scraper import scraper_manager, ScraperType

@router.post("/scraping/jobs")
async def create_scraping_job(
    query: str,
    scraper_type: str = "auto",
    max_pages: int = 5
):
    config = ScrapingConfig(max_pages=max_pages)
    job_id = await scraper_manager.create_job(
        query=query,
        scraper_type=scraper_type,
        config=config
    )
    return {"job_id": job_id}

@router.get("/scraping/jobs/{job_id}")
async def get_scraping_job(job_id: str):
    job_info = await scraper_manager.get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_info

@router.get("/scraping/jobs/{job_id}/result")
async def get_scraping_result(job_id: str):
    result = await scraper_manager.get_job_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not available")
    return {
        "status": result.status.value,
        "companies": result.companies,
        "contacts": result.contacts,
        "total_records": result.total_records_found,
        "execution_time": result.execution_time
    }
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Increase delays between requests
   - Use adaptive rate limiting
   - Implement exponential backoff

2. **Blocked Requests**
   - Rotate user agents
   - Use proxy servers
   - Implement CAPTCHA solving

3. **Data Quality**
   - Improve extraction patterns
   - Add data validation
   - Implement data cleaning

4. **Performance Issues**
   - Optimize selector patterns
   - Reduce concurrent requests
   - Use caching strategies

### Debug Mode

```python
# Enable debug logging
logging.getLogger('app.services.scraper').setLevel(logging.DEBUG)

# Use debug configuration
debug_config = ScrapingConfig(
    max_pages=1,
    delay_between_requests=5.0,
    timeout=60,
    max_retries=1
)
```

## Future Enhancements

1. **Additional Sources**
   - Facebook Business Pages
   - Yellow Pages
   - Industry-specific directories

2. **Advanced Features**
   - Machine learning for data extraction
   - Natural language processing
   - Image recognition for logos

3. **Performance Improvements**
   - Distributed scraping
   - Browser automation optimization
   - Intelligent caching

4. **Integration Enhancements**
   - Real-time data streaming
   - Webhook notifications
   - Advanced analytics

This documentation provides a comprehensive guide to using the Web Scraping Engine. For additional support or feature requests, please refer to the project documentation or contact the development team.