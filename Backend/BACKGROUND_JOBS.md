# Background Job Processing System

This document describes the background job processing system implemented using Celery with Redis as the message broker and result backend.

## Overview

The background job processing system handles asynchronous tasks for:
- Web scraping operations
- Data processing and enrichment
- Lead scoring calculations
- Analytics report generation
- System maintenance tasks

## Architecture

### Components

1. **Celery Application** (`app/core/celery_app.py`)
   - Main Celery configuration
   - Task routing and queues
   - Beat schedule for periodic tasks

2. **Job Manager** (`app/services/background_jobs/job_manager.py`)
   - Centralized job lifecycle management
   - Job status tracking and progress updates
   - Job statistics and monitoring

3. **Task Modules**
   - `scraping_tasks.py` - Web scraping operations
   - `data_processing_tasks.py` - Data processing and enrichment
   - `analytics_tasks.py` - Analytics and reporting
   - `maintenance_tasks.py` - System maintenance

4. **API Endpoints** (`app/api/jobs.py`)
   - RESTful API for job management
   - Job submission, status checking, and cancellation

### Queue Structure

- **scraping** - Web scraping tasks (high priority)
- **processing** - Data processing tasks (normal priority)
- **analytics** - Analytics and reporting tasks (normal priority)
- **maintenance** - System maintenance tasks (low priority)

## Installation and Setup

### Prerequisites

- Redis server running
- Python dependencies installed (`celery`, `redis`)

### Starting Services

#### Option 1: Docker Compose (Recommended)

```bash
# Start Redis and Celery services
docker-compose -f docker-compose.jobs.yml up -d

# View logs
docker-compose -f docker-compose.jobs.yml logs -f

# Stop services
docker-compose -f docker-compose.jobs.yml down
```

#### Option 2: Manual Setup

1. **Start Redis**
   ```bash
   redis-server
   ```

2. **Start Celery Worker**
   ```bash
   celery -A app.core.celery_app worker --loglevel=info --concurrency=4
   ```

3. **Start Celery Beat (for periodic tasks)**
   ```bash
   celery -A app.core.celery_app beat --loglevel=info
   ```

4. **Start Flower (monitoring, optional)**
   ```bash
   celery -A app.core.celery_app flower --port=5555
   ```

#### Option 3: Python Scripts

```bash
# Start worker
python worker.py

# Start beat scheduler
python beat.py
```

## API Usage

### Job Submission

#### Scraping Jobs

```bash
# Scrape multiple companies
curl -X POST "http://localhost:8000/api/v1/jobs/scrape/companies" \
  -H "Content-Type: application/json" \
  -d '{
    "company_urls": ["https://example.com", "https://company2.com"],
    "priority": "high"
  }'

# Scrape single company
curl -X POST "http://localhost:8000/api/v1/jobs/scrape/company" \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://example.com",
    "priority": "normal"
  }'

# Batch scraping
curl -X POST "http://localhost:8000/api/v1/jobs/scrape/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["tech startups", "fintech companies"],
    "max_results_per_query": 10
  }'
```

#### Data Processing Jobs

```bash
# Process scraped data
curl -X POST "http://localhost:8000/api/v1/jobs/process/data" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["comp_123", "comp_456"]
  }'

# Calculate lead scores
curl -X POST "http://localhost:8000/api/v1/jobs/process/scores" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["comp_123", "comp_456"]
  }'

# Enrich company data
curl -X POST "http://localhost:8000/api/v1/jobs/process/enrich" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["comp_123", "comp_456"]
  }'
```

#### Analytics Jobs

```bash
# Generate analytics report
curl -X POST "http://localhost:8000/api/v1/jobs/analytics/report" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["comp_123", "comp_456"],
    "report_type": "comprehensive"
  }'

# Business intelligence analysis
curl -X POST "http://localhost:8000/api/v1/jobs/analytics/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["comp_123", "comp_456"]
  }'
```

### Job Management

```bash
# Get job status
curl "http://localhost:8000/api/v1/jobs/status/{job_id}"

# List jobs
curl "http://localhost:8000/api/v1/jobs/list?status=running&limit=10"

# Cancel job
curl -X DELETE "http://localhost:8000/api/v1/jobs/cancel/{job_id}"

# Get statistics
curl "http://localhost:8000/api/v1/jobs/statistics"
```

## Job Status and Progress

### Job Statuses

- `pending` - Job is queued but not started
- `running` - Job is currently executing
- `completed` - Job finished successfully
- `failed` - Job failed with an error
- `cancelled` - Job was cancelled
- `retry` - Job is being retried

### Progress Tracking

Jobs report progress with:
- Current step number
- Total steps
- Percentage complete
- Status message
- Detailed progress information

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Celery Configuration
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
```

### Queue Configuration

Queues are configured in `celery_app.py`:

```python
task_routes = {
    'app.services.background_jobs.scraping_tasks.*': {'queue': 'scraping'},
    'app.services.background_jobs.data_processing_tasks.*': {'queue': 'processing'},
    'app.services.background_jobs.analytics_tasks.*': {'queue': 'analytics'},
    'app.services.background_jobs.maintenance_tasks.*': {'queue': 'maintenance'},
}
```

## Monitoring

### Flower Dashboard

Access the Flower monitoring dashboard at `http://localhost:5555` to:
- View active workers and tasks
- Monitor task execution times
- Check queue lengths
- View task history and statistics

### Job Statistics API

The `/jobs/statistics` endpoint provides:
- Total jobs by status
- Average execution times
- Success/failure rates
- Queue lengths

## Error Handling

### Retry Logic

- Failed tasks are automatically retried up to 3 times
- Exponential backoff with jitter
- Different retry strategies for different error types

### Error Reporting

- Detailed error messages in job results
- Error categorization (network, data, system)
- Error notifications for critical failures

## Maintenance

### Periodic Tasks

Configured in the beat schedule:

- **Job Cleanup** - Remove expired job data (daily)
- **Statistics Update** - Update job statistics (hourly)
- **Health Check** - System health monitoring (every 30 minutes)
- **Database Optimization** - Database maintenance (weekly)

### Manual Maintenance

```bash
# Clean up old data
curl -X POST "http://localhost:8000/api/v1/jobs/maintenance/cleanup?older_than_days=90"

# System health check
curl -X POST "http://localhost:8000/api/v1/jobs/maintenance/health-check"

# Database optimization
curl -X POST "http://localhost:8000/api/v1/jobs/maintenance/optimize-db"
```

## Performance Tuning

### Worker Configuration

- **Concurrency**: Adjust based on CPU cores and task types
- **Prefetch**: Control how many tasks workers prefetch
- **Memory limits**: Set memory limits to prevent OOM issues

### Queue Management

- **Priority queues**: Use different priorities for different task types
- **Queue routing**: Route tasks to appropriate queues
- **Queue monitoring**: Monitor queue lengths and processing times

### Redis Optimization

- **Memory configuration**: Tune Redis memory settings
- **Persistence**: Configure appropriate persistence settings
- **Connection pooling**: Use connection pooling for better performance

## Security Considerations

- **Authentication**: Secure API endpoints with proper authentication
- **Authorization**: Implement role-based access control
- **Input validation**: Validate all job parameters
- **Resource limits**: Set limits on job execution time and resources
- **Network security**: Secure Redis and Celery communications

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   - Check Redis server status
   - Verify connection settings
   - Check network connectivity

2. **Worker Not Processing Tasks**
   - Check worker logs
   - Verify queue configuration
   - Check task routing

3. **High Memory Usage**
   - Monitor worker memory usage
   - Adjust concurrency settings
   - Check for memory leaks

4. **Slow Task Execution**
   - Profile task performance
   - Check database connections
   - Monitor external API calls

### Debugging

```bash
# Check Celery status
celery -A app.core.celery_app inspect active
celery -A app.core.celery_app inspect stats

# Monitor queues
celery -A app.core.celery_app inspect active_queues

# Check worker status
celery -A app.core.celery_app inspect ping
```

## Development

### Adding New Tasks

1. Create task function in appropriate module
2. Register task with Celery
3. Add API endpoint if needed
4. Update job manager integration
5. Add tests

### Testing

```bash
# Run task tests
pytest tests/test_background_jobs.py

# Test specific task
pytest tests/test_background_jobs.py::test_scraping_task
```

## Production Deployment

### Scaling

- **Horizontal scaling**: Add more worker instances
- **Queue-specific workers**: Dedicated workers for different queues
- **Load balancing**: Distribute tasks across multiple workers

### Monitoring

- **Metrics collection**: Collect and analyze job metrics
- **Alerting**: Set up alerts for failures and performance issues
- **Logging**: Centralized logging for all components

### High Availability

- **Redis clustering**: Use Redis cluster for high availability
- **Worker redundancy**: Run multiple worker instances
- **Health checks**: Implement comprehensive health checks