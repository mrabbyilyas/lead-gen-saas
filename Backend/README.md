# Lead Generation SaaS Backend

A comprehensive FastAPI-based backend system for lead generation and management with web scraping capabilities.

## Features

- **FastAPI Framework**: High-performance async API with automatic documentation
- **Supabase Integration**: PostgreSQL database with real-time capabilities
- **Web Scraping**: BeautifulSoup and Selenium for data extraction
- **Task Queue**: Celery with Redis for background processing
- **Lead Management**: CRUD operations with advanced filtering
- **Analytics Dashboard**: Real-time metrics and performance tracking
- **Data Export**: Multiple formats (CSV, Excel, JSON)
- **Rate Limiting**: API protection and usage control
- **Health Monitoring**: Comprehensive health checks

## Technology Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: Supabase (PostgreSQL)
- **Cache/Queue**: Redis, Celery
- **Scraping**: BeautifulSoup4, Selenium, Requests
- **Data Processing**: Pandas, NumPy
- **Export**: OpenPyXL, XlsxWriter
- **Security**: Passlib, Python-JOSE

## Project Structure

```
Backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py
│   │           ├── scrape.py
│   │           ├── leads.py
│   │           ├── analytics.py
│   │           └── export.py
│   └── core/
│       ├── __init__.py
│       ├── config.py
│       └── database.py
├── main.py
├── requirements.txt
├── .env
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Redis server
- Supabase account and project

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lead-gen-saas/Backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   
   Create a `.env` file in the root directory:
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   
   # Redis Configuration
   REDIS_URL=redis://localhost:6379
   
   # Application Configuration
   ENVIRONMENT=development
   DEBUG=True
   API_VERSION=v1
   SECRET_KEY=your-secret-key-change-in-production
   
   # Rate Limiting
   RATE_LIMIT_PER_MINUTE=60
   
   # Scraping Configuration
   MAX_CONCURRENT_SCRAPES=5
   SCRAPE_DELAY_SECONDS=1.0
   
   # Celery Configuration
   CELERY_BROKER_URL=redis://localhost:6379
   CELERY_RESULT_BACKEND=redis://localhost:6379
   ```

5. **Start the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Monitoring
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with service status

### Lead Management
- `GET /api/v1/leads/` - Get leads with filtering and pagination
- `GET /api/v1/leads/{lead_id}` - Get specific lead
- `PUT /api/v1/leads/{lead_id}/score` - Update lead scoring
- `POST /api/v1/leads/bulk-update` - Bulk update leads

### Web Scraping
- `POST /api/v1/scrape/start` - Start scraping job
- `GET /api/v1/scrape/status/{job_id}` - Get scraping status

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard metrics
- `GET /api/v1/analytics/trends` - Lead trends analysis
- `GET /api/v1/analytics/performance` - Scraping performance
- `GET /api/v1/analytics/export-stats` - Export statistics

### Data Export
- `POST /api/v1/export/csv` - Export to CSV
- `POST /api/v1/export/excel` - Export to Excel
- `POST /api/v1/export/json` - Export to JSON
- `GET /api/v1/export/history` - Export history
- `GET /api/v1/export/download/{export_id}` - Download export

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
black .
flake8 .
```

### Starting Celery Worker
```bash
celery -A app.celery worker --loglevel=info
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_KEY` | Supabase anon key | Required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `ENVIRONMENT` | Application environment | `development` |
| `DEBUG` | Debug mode | `True` |
| `API_VERSION` | API version | `v1` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `MAX_CONCURRENT_SCRAPES` | Max concurrent scraping jobs | `5` |
| `SCRAPE_DELAY_SECONDS` | Delay between scrape requests | `1.0` |

## Security

- Environment variables for sensitive data
- Rate limiting on API endpoints
- Input validation with Pydantic
- CORS configuration
- Secure headers

## Monitoring

- Health check endpoints
- Application metrics
- Error logging
- Performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.