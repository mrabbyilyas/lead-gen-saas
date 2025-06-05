# Backend Functional Requirements - Lead Generation Tool

## 📋 Overview

This document outlines the functional requirements for the backend system of a lead generation tool inspired by saasquatchleads.com. The system is designed to scrape, process, and analyze business data to generate qualified sales leads.

## 🏗️ Project Structure (with Supabase)

```
leadgen-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration and Supabase credentials
│   ├── supabase_client.py         # Supabase client initialization
│   └── core/
│       ├── __init__.py
│       ├── security.py            # Authentication and security
│       └── exceptions.py          # Custom exception handlers
│
├── app/models/
│   ├── __init__.py
│   ├── company.py                 # Company Pydantic models
│   ├── contact.py                 # Contact Pydantic models
│   ├── scraped_data.py           # Raw scraped data models
│   └── job.py                    # Scraping job models
│
├── app/database/
│   ├── __init__.py
│   ├── supabase_tables.sql        # Supabase table creation scripts
│   ├── migrations/                # SQL migration files
│   └── seed_data.sql             # Sample data for testing
│
├── app/services/
│   ├── __init__.py
│   ├── supabase_service.py        # Supabase CRUD operations wrapper
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── base_scraper.py        # Abstract base scraper class
│   │   ├── google_scraper.py      # Google My Business scraper
│   │   ├── linkedin_scraper.py    # LinkedIn company scraper
│   │   ├── website_scraper.py     # Company website scraper
│   │   └── directory_scraper.py   # Business directory scraper
│   │
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── data_cleaner.py        # Data validation and cleaning
│   │   ├── data_enricher.py       # Data enrichment engine
│   │   ├── deduplicator.py        # Duplicate detection and removal
│   │   └── lead_scorer.py         # Lead scoring algorithm
│   │
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── growth_detector.py     # Business growth signals
│   │   ├── tech_stack_analyzer.py # Technology stack detection
│   │   └── pain_point_detector.py # Pain points identification
│   │
│   └── export/
│       ├── __init__.py
│       ├── csv_exporter.py        # CSV export functionality
│       └── api_integration.py     # CRM integration APIs
│├── app/schemas/
│   ├── __init__.py
│   ├── company.py                 # Pydantic schemas for company
│   ├── contact.py                 # Pydantic schemas for contact
│   ├── search.py                  # Search request/response schemas
│   └── job.py                    # Job status schemas
│
├── app/api/
│   ├── __init__.py
│   ├── deps.py                    # API dependencies (Supabase client injection)
│   └── v1/
│       ├── __init__.py
│       ├── scraping.py            # Scraping endpoints
│       ├── leads.py               # Lead management endpoints  
│       ├── export.py              # Data export endpoints
│       ├── realtime.py            # Real-time subscriptions
│       └── health.py              # Health check endpoints
│
├── app/utils/
│   ├── __init__.py
│   ├── email_validator.py         # Email validation utilities
│   ├── phone_formatter.py         # Phone number formatting
│   ├── url_utils.py              # URL parsing and validation
│   └── rate_limiter.py           # Rate limiting utilities
│
├── app/workers/
│   ├── __init__.py
│   ├── scraping_worker.py         # Background scraping jobs
│   └── processing_worker.py       # Background data processing
│
├── app/tests/
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── test_api/
│   ├── test_services/
│   └── test_supabase/            # Supabase integration tests
│
├── supabase/
│   ├── migrations/               # Supabase migrations
│   ├── seed.sql                 # Initial data
│   └── config.toml              # Supabase configuration
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── docs/
│   ├── api.md                    # API documentation
│   ├── supabase_setup.md        # Supabase setup guide
│   └── deployment.md             # Deployment guide
│
├── .env.example                  # Environment variables template
├── .gitignore
├── requirements.txt              # Python dependencies
├── README.md
└── Dockerfile                    # Main Dockerfile
```

## 📊 1. Data Collection Module

### 1.1 Web Scraping Engine

#### Core Scraping Capabilities
```python
REQUIRED_SOURCES = [
    "Google My Business",
    "LinkedIn Company Pages", 
    "Company Websites (Contact Pages)",
    "Yellow Pages/Business Directories"
]

SCRAPING_FUNCTIONS = {
    "company_basic_info": {
        "inputs": ["industry", "location", "company_size"],
        "outputs": ["company_name", "address", "phone", "website"],
        "rate_limit": "1 request/second",
        "retry_logic": "3 attempts with exponential backoff"
    },
    
    "contact_extraction": {
        "inputs": ["company_website_url"],
        "outputs": ["emails", "phone_numbers", "social_links"],
        "patterns": {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            "linkedin": r"linkedin\.com/company/[\w-]+"
        }
    }
}
```

#### Rate Limiting & Ethics
```python
SCRAPING_CONSTRAINTS = {
    "requests_per_minute": 30,
    "concurrent_requests": 3,
    "user_agent_rotation": True,
    "respect_robots_txt": True,
    "request_delay": "1-3 seconds random",
    "session_management": "rotate every 50 requests"
}
```

### 1.2 Data Sources Configuration

| Source | Priority | Data Types | Rate Limit | Error Handling |
|--------|----------|------------|------------|----------------|
| Google My Business | High | Basic company info, reviews | 30/min | Retry with backoff |
| LinkedIn Company | High | Employee count, company updates | 20/min | Fallback to website |
| Company Websites | Medium | Contact info, team pages | 60/min | Skip if blocked |
| Business Directories | Low | Secondary validation | 100/min | Best effort |

## 📈 2. Data Processing Pipeline

### 2.1 Data Validation & Cleaning

```python
DATA_VALIDATION_RULES = {
    "company_name": {
        "required": True,
        "min_length": 2,
        "max_length": 100,
        "validation": "remove_special_chars, title_case"
    },
    
    "email": {
        "format_validation": "valid_email_regex",
        "domain_validation": "check_mx_record",
        "deduplication": "case_insensitive"
    },
    
    "phone": {
        "format_standardization": "international_format",
        "validation": "valid_phone_number_library"
    },
    
    "website": {
        "url_validation": "valid_url_format",
        "accessibility_check": "http_status_200",
        "ssl_check": "https_preferred"
    }
}
```

### 2.2 Data Enrichment Engine

```python
ENRICHMENT_FEATURES = {
    "company_size_estimation": {
        "method": "linkedin_employee_count",
        "fallback": "website_job_postings_count",
        "categories": ["1-10", "11-50", "51-200", "201-1000", "1000+"]
    },
    
    "industry_classification": {
        "method": "business_description_nlp",
        "model": "industry_classifier_model",
        "confidence_threshold": 0.7
    },
    
    "technology_stack_detection": {
        "method": "website_analysis",
        "sources": ["builtwith_api", "wappalyzer_patterns"],
        "categories": ["frontend", "backend", "analytics", "marketing"]
    }
}
```

## 🎯 3. Lead Scoring & Intelligence

### 3.1 Lead Scoring Algorithm

```python
SCORING_CRITERIA = {
    "contact_completeness": {
        "weight": 0.25,
        "scoring": {
            "email_found": 20,
            "phone_found": 15,
            "decision_maker_contact": 25,
            "multiple_contacts": 10
        }
    },
    
    "business_indicators": {
        "weight": 0.35,
        "scoring": {
            "company_size_match": 30,
            "industry_relevance": 25,
            "technology_match": 20,
            "growth_signals": 25
        }
    },
    
    "data_quality": {
        "weight": 0.25,
        "scoring": {
            "verified_email": 20,
            "active_website": 15,
            "recent_activity": 20,
            "social_presence": 10
        }
    },
    
    "engagement_potential": {
        "weight": 0.15,
        "scoring": {
            "job_postings_active": 15,
            "funding_news": 20,
            "expansion_signals": 10
        }
    }
}

LEAD_SCORE_RANGE = {
    "min": 0,
    "max": 100,
    "categories": {
        "hot": "80-100",
        "warm": "60-79", 
        "cold": "40-59",
        "poor": "0-39"
    }
}
```

### 3.2 Business Intelligence Features

```python
INTELLIGENCE_MODULES = {
    "growth_signals_detector": {
        "indicators": [
            "recent_job_postings",
            "funding_announcements", 
            "new_office_locations",
            "product_launches",
            "hiring_spree"
        ],
        "sources": ["company_news", "job_boards", "press_releases"]
    },
    
    "pain_points_identifier": {
        "method": "nlp_analysis",
        "sources": ["company_blog", "job_descriptions", "reviews"],
        "categories": ["technology", "processes", "scaling", "compliance"]
    }
}
```

## 🗄️ Supabase Database Setup

### Supabase Configuration

#### Environment Variables
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Application Configuration  
ENVIRONMENT=development
DEBUG=True
API_VERSION=v1
```

#### Supabase Client Initialization
```python
# app/supabase_client.py
from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """Initialize and return Supabase client"""
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
    )

# Dependency for FastAPI endpoints
async def get_supabase() -> Client:
    """FastAPI dependency to inject Supabase client"""
    return get_supabase_client()
```

### Database Schema (Supabase SQL)

#### Create Tables with RLS (Row Level Security)
```sql
-- Enable RLS and create custom types
CREATE TYPE company_size_enum AS ENUM ('1-10', '11-50', '51-200', '201-1000', '1000+');
CREATE TYPE scrape_type_enum AS ENUM ('contact', 'company_info', 'tech_stack', 'growth_signals');
CREATE TYPE job_status_enum AS ENUM ('pending', 'running', 'completed', 'failed');

-- Companies Table
CREATE TABLE companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    size_category company_size_enum,
    website VARCHAR(255),
    description TEXT,
    location JSONB DEFAULT '{}',
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT companies_name_check CHECK (length(trim(name)) > 0)
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- Contacts Table
CREATE TABLE contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100),
    title VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    linkedin_url VARCHAR(255),
    is_decision_maker BOOLEAN DEFAULT FALSE,
    confidence_score FLOAT DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_email_per_company UNIQUE (company_id, email),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}

### 4.1 Supabase Real-time Features

#### Real-time Lead Updates
```python
# app/api/v1/realtime.py
from fastapi import APIRouter, WebSocket, Depends
from supabase import Client
from app.api.deps import get_supabase

router = APIRouter()

@router.websocket("/ws/leads")
async def websocket_leads_updates(
    websocket: WebSocket,
    supabase: Client = Depends(get_supabase)
):
    """WebSocket endpoint for real-time lead updates"""
    await websocket.accept()
    
    # Subscribe to changes in companies table
    def handle_company_changes(payload):
        # Send updates to connected clients
        websocket.send_json({
            "type": "company_update",
            "data": payload
        })
    
    # Set up Supabase real-time subscription
    supabase.table('companies').on('*', handle_company_changes).subscribe()
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        # Clean up subscription
        supabase.remove_all_subscriptions()
```

#### Database Functions for Analytics
```sql
-- Create database function for score distribution
CREATE OR REPLACE FUNCTION get_score_distribution()
RETURNS TABLE (
    score_range TEXT,
    count BIGINT
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN lead_score >= 80 THEN 'Hot (80-100)'
            WHEN lead_score >= 60 THEN 'Warm (60-79)'
            WHEN lead_score >= 40 THEN 'Cold (40-59)'
            ELSE 'Poor (0-39)'
        END as score_range,
        COUNT(*) as count
    FROM companies
    GROUP BY 1
    ORDER BY MIN(lead_score) DESC;
END;
$ LANGUAGE plpgsql;

-- Create function for lead search with scoring
CREATE OR REPLACE FUNCTION search_leads(
    p_industry TEXT DEFAULT NULL,
    p_location TEXT DEFAULT NULL,
    p_min_score INTEGER DEFAULT 0,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    name VARCHAR,
    industry VARCHAR,
    lead_score INTEGER,
    contact_count BIGINT,
    location JSONB,
    created_at TIMESTAMPTZ
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.industry,
        c.lead_score,
        COUNT(ct.id) as contact_count,
        c.location,
        c.created_at
    FROM companies c
    LEFT JOIN contacts ct ON c.id = ct.company_id
    WHERE 
        (p_industry IS NULL OR c.industry ILIKE '%' || p_industry || '%')
        AND (p_location IS NULL OR c.location->>'city' ILIKE '%' || p_location || '%')
        AND c.lead_score >= p_min_score
    GROUP BY c.id, c.name, c.industry, c.lead_score, c.location, c.created_at
    ORDER BY c.lead_score DESC, c.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$ LANGUAGE plpgsql;
```

### 4.2 Data Deduplication Strategy

```python
DEDUPLICATION_STRATEGY = {
    "company_matching": {
        "primary_key": "company_name + domain",
        "fuzzy_matching": {
            "algorithm": "levenshtein_distance",
            "threshold": 0.85,
            "fields": ["name", "website", "phone"]
        }
    },
    
    "contact_matching": {
        "primary_key": "email",
        "secondary_matching": "name + company_id",
        "merge_strategy": "keep_most_complete_record"
    }
}
```

## 🔌 5. API Endpoints (Supabase Integration)

### 5.1 Core API Routes with Supabase

#### Scraping Operations
```python
# app/api/v1/scraping.py
from fastapi import APIRouter, Depends, BackgroundTasks
from supabase import Client
from app.api.deps import get_supabase
from app.services.supabase_service import SupabaseService
from app.schemas.search import SearchRequest, SearchResponse
from app.workers.scraping_worker import start_scraping_job

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def initiate_search(
    search_request: SearchRequest,
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase)
):
    """Initiate lead search with Supabase job tracking"""
    service = SupabaseService(supabase)
    
    # Create job record in Supabase
    job_data = {
        "search_criteria": search_request.model_dump(),
        "status": "pending"
    }
    job = await service.create_job(job_data)
    
    # Start background scraping task
    background_tasks.add_task(
        start_scraping_job, 
        job["id"], 
        search_request,
        supabase
    )
    
    return SearchResponse(
        job_id=job["id"],
        status="initiated",
        estimated_completion="2025-06-03T10:30:00Z"
    )

@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get real-time job status from Supabase"""
    response = supabase.table('scraping_jobs').select('*').eq(
        'id', job_id
    ).single().execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = response.data
    return {
        "job_id": job["id"],
        "status": job["status"],
        "progress": job["progress"],
        "results_count": job["results_count"],
        "errors": job["errors"],
        "estimated_completion": job.get("estimated_completion")
    }
```

#### Lead Management with Supabase
```python
# app/api/v1/leads.py
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.api.deps import get_supabase
from app.services.supabase_service import SupabaseService

router = APIRouter()

@router.get("/")
async def get_leads(
    score_min: int = Query(0, ge=0, le=100),
    industry: str = Query(None),
    location: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase)
):
    """Get leads using Supabase RPC for optimized queries"""
    
    # Use Supabase RPC function for complex queries
    response = supabase.rpc('search_leads', {
        'p_industry': industry,
        'p_location': location,
        'p_min_score': score_min,
        'p_limit': limit,
        'p_offset': offset
    }).execute()
    
    # Get total count for pagination
    count_response = supabase.table('companies').select(
        'id', count='exact'
    ).execute()
    
    return {
        "leads": response.data,
        "total_count": count_response.count,
        "pagination": {
            "has_next": len(response.data) == limit,
            "has_prev": offset > 0,
            "next_offset": offset + limit if len(response.data) == limit else None
        }
    }

@router.get("/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get detailed lead information with joins"""
    service = SupabaseService(supabase)
    
    # Get company with related data
    company_response = supabase.table('companies').select(
        '*, contacts(*), scraped_data(*)'
    ).eq('id', lead_id).single().execute()
    
    if not company_response.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    company = company_response.data
    
    # Calculate score breakdown (simplified for demo)
    score_breakdown = {
        "contact_completeness": min(len(company.get('contacts', [])) * 10, 25),
        "business_indicators": 30,  # Placeholder
        "data_quality": 25,         # Placeholder  
        "engagement_potential": 15, # Placeholder
        "total": company.get('lead_score', 0)
    }
    
    return {
        "company": {
            "id": company["id"],
            "name": company["name"],
            "industry": company["industry"],
            "size_category": company["size_category"],
            "website": company["website"],
            "description": company["description"],
            "location": company["location"],
            "lead_score": company["lead_score"]
        },
        "contacts": company.get("contacts", []),
        "intelligence": {
            "growth_signals": ["Recent hiring spree", "Series B funding"],
            "technology_stack": ["React", "Node.js", "AWS"],
            "pain_points": ["Scaling challenges", "Legacy system migration"]
        },
        "score_breakdown": score_breakdown
    }
```

#### Export with Supabase
```python
# app/api/v1/export.py
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from supabase import Client
from app.api.deps import get_supabase
import csv
import io

router = APIRouter()

@router.get("/csv")
async def export_leads_csv(
    lead_ids: str = Query(..., description="Comma-separated lead IDs"),
    fields: str = Query("name,email,phone,score", description="Comma-separated field names"),
    supabase: Client = Depends(get_supabase)
):
    """Export leads to CSV using Supabase data"""
    
    # Parse parameters
    id_list = [id.strip() for id in lead_ids.split(',')]
    field_list = [field.strip() for field in fields.split(',')]
    
    # Get data from Supabase
    response = supabase.table('companies').select(
        'id, name, industry, lead_score, website, contacts(name, email, phone, title)'
    ).in_('id', id_list).execute()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = ['company_name']
    if 'email' in field_list:
        headers.append('email')
    if 'phone' in field_list:
        headers.append('phone')
    if 'score' in field_list:
        headers.append('lead_score')
    if 'industry' in field_list:
        headers.append('industry')
    
    writer.writerow(headers)
    
    # Write data rows
    for company in response.data:
        contacts = company.get('contacts', [{}])
        main_contact = contacts[0] if contacts else {}
        
        row = [company['name']]
        if 'email' in field_list:
            row.append(main_contact.get('email', ''))
        if 'phone' in field_list:
            row.append(main_contact.get('phone', ''))
        if 'score' in field_list:
            row.append(company['lead_score'])
        if 'industry' in field_list:
            row.append(company.get('industry', ''))
            
        writer.writerow(row)
    
    # Return CSV file
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )
```

## ⚡ 6. Performance & Scalability

### 6.1 Performance Requirements

| Metric | Target | Measurement |
|--------|---------|-------------|
| API Response Time | < 500ms | 95th percentile |
| Search Initiation | < 200ms | Average |
| Lead Retrieval | < 1000ms | With full data |
| Scraping Throughput | 100 companies/hour | Sustained rate |
| Success Rate | > 85% | Valid data extraction |
| Concurrent Users | 10 users | Without degradation |

### 6.2 Error Handling Strategy

```python
ERROR_HANDLING = {
    "scraping_failures": {
        "retry_strategy": "exponential_backoff",
        "max_retries": 3,
        "fallback_sources": "alternative_scrapers",
        "circuit_breaker": "after_5_consecutive_failures"
    },
    
    "api_errors": {
        "validation_errors": "400 with detailed field messages",
        "authentication_errors": "401 with clear auth requirements",
        "rate_limit_exceeded": "429 with retry_after header",
        "server_errors": "500 with unique error_id for tracking"
    },
    
    "data_quality_issues": {
        "invalid_emails": "flag_for_manual_review",
        "missing_contacts": "lower_lead_score_accordingly", 
        "blocked_websites": "mark_source_unavailable",
        "duplicate_data": "merge_with_existing_record"
    }
}
```

### 6.3 Monitoring & Logging

```python
MONITORING_METRICS = {
    "business_metrics": [
        "leads_generated_per_hour",
        "average_lead_score",
        "data_quality_percentage",
        "source_success_rates"
    ],
    
    "technical_metrics": [
        "api_response_times",
        "error_rates_by_endpoint",
        "database_query_performance",
        "scraping_job_queue_length"
    ],
    
    "alerting_thresholds": {
        "api_error_rate": "> 5%",
        "scraping_success_rate": "< 80%",
        "database_response_time": "> 2 seconds",
        "queue_backlog": "> 100 jobs"
    }
}
```

## 🎯 7. Minimum Viable Product (5-Hour Scope with Supabase)

### Supabase Advantages for 5-Hour Sprint:
- **No database setup time** - Instant PostgreSQL with admin UI
- **Auto-generated REST API** - Reduces backend coding time
- **Real-time features** - WebSocket connections out-of-the-box
- **Built-in authentication** - No need to implement JWT from scratch
- **Dashboard UI** - Monitor data in real-time during development

### Priority 1 (Hours 1-3): Core Features with Supabase
- [x] **Supabase project setup** (15 minutes)
- [x] **Database schema creation** via Supabase SQL Editor (30 minutes)
- [x] **Basic company search** by industry + location
- [x] **Google My Business scraping** integration
- [x] **Contact page scraping** for emails/phones
- [x] **Simple lead scoring** (contact completeness only)
- [x] **Supabase CRUD operations** via Python client
- [x] **Background job tracking** in Supabase tables

### Priority 2 (Hour 4): Enhancement with Supabase Features
- [x] **Real-time job status updates** via Supabase subscriptions
- [x] **Data validation** and basic cleaning
- [x] **Simple deduplication** using Supabase RPC functions
- [x] **Lead retrieval API** with Supabase pagination
- [x] **CSV export** functionality
- [x] **Supabase dashboard** for monitoring

### Priority 3 (Hour 5): Polish & Demo Prep
- [x] **API documentation** with FastAPI auto-docs
- [x] **Docker containerization** with Supabase integration
- [x] **Health check endpoints**
- [x] **Demo data seeding** via Supabase
- [x] **Real-time demo** showing live updates

### Quick Implementation Example

#### Main Application Setup
```python
# app/main.py
from fastapi import FastAPI, Depends
from supabase import create_client, Client
from app.config import settings
from app.api.v1 import scraping, leads, export

app = FastAPI(title="LeadGen Pro API", version="1.0.0")

# Supabase client
def get_supabase_client() -> Client:
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )

# Include routers
app.include_router(scraping.router, prefix="/api/v1/scrape", tags=["scraping"])
app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

@app.get("/health")
async def health_check(supabase: Client = Depends(get_supabase_client)):
    """Health check with Supabase connectivity test"""
    try:
        response = supabase.table('companies').select('id').limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-06-03T10:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }
```

#### Simple Scraping Implementation
```python
# app/services/scraper/google_scraper.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

class GoogleBusinessScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; LeadGen/1.0)'
        })
    
    async def search_businesses(
        self, 
        industry: str, 
        location: str, 
        max_results: int = 50
    ) -> List[Dict]:
        """Scrape Google My Business listings"""
        
        # Simplified scraping logic for demo
        # In production, use proper Google Places API
        
        companies = []
        
        # Mock data for MVP demo
        for i in range(min(max_results, 10)):
            company = {
                "name": f"{industry.title()} Corp {i+1}",
                "industry": industry,
                "location": {"city": location.split(",")[0], "state": "CA"},
                "website": f"https://{industry}corp{i+1}.com",
                "phone": f"+1-555-{100+i:03d}-{1000+i:04d}",
                "description": f"Leading {industry} company in {location}"
            }
            companies.append(company)
        
        return companies
    
    async def extract_contacts(self, website_url: str) -> List[Dict]:
        """Extract contacts from company website"""
        try:
            response = self.session.get(f"{website_url}/contact", timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Simple email extraction
            emails = []
            email_elements = soup.find_all(string=lambda text: '@' in text if text else False)
            
            for element in email_elements[:3]:  # Limit to 3 emails
                import re
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', element)
                if email_match:
                    emails.append({
                        "email": email_match.group(),
                        "name": "Contact Person",
                        "title": "Team Member"
                    })
            
            return emails
            
        except Exception as e:
            print(f"Error extracting contacts from {website_url}: {e}")
            return []
```

### Post-MVP Enhancements (Future Iterations)
- [ ] **Advanced lead scoring** with multiple factors using Supabase RPC
- [ ] **LinkedIn company data** integration
- [ ] **Technology stack detection** via website analysis
- [ ] **Growth signals detection** using news APIs
- [ ] **Advanced data enrichment** with external APIs
- [ ] **CRM integration APIs** (HubSpot, Salesforce)
- [ ] **Real-time notifications** via Supabase Edge Functions
- [ ] **Advanced analytics dashboard** with Supabase views
- [ ] **Multi-tenant support** using Supabase RLS
- [ ] **Automated lead scoring** using machine learning

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance async API |
| Database | PostgreSQL/SQLite | Data persistence |
| Background Jobs | Celery + Redis | Async task processing |
| Web Scraping | BeautifulSoup + Requests | Data extraction |
| Data Validation | Pydantic | Schema validation |
| Authentication | JWT | API security |
| Documentation | OpenAPI/Swagger | Auto-generated docs |
| Containerization | Docker | Deployment |
| Testing | Pytest | Unit and integration tests |

## 📚 Dependencies

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Database
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9

# Web Scraping
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
fake-useragent==1.4.0

# Background Tasks
celery==5.3.4
redis==5.0.1

# Data Processing
pandas==2.1.3
phonenumbers==8.13.25
email-validator==2.1.0

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
```

This comprehensive backend system provides a solid foundation for a lead generation tool that can be built within the 5-hour constraint while remaining scalable for future enhancements.)
);

-- Scraped Data Table  
CREATE TABLE scraped_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    source_url VARCHAR(500),
    data_type scrape_type_enum NOT NULL,
    raw_data JSONB DEFAULT '{}',
    processed_data JSONB DEFAULT '{}',
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending'
);

-- Scraping Jobs Table
CREATE TABLE scraping_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    status job_status_enum DEFAULT 'pending',
    search_criteria JSONB DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_duration INTERVAL
);

-- Create indexes for performance
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_size ON companies(size_category);
CREATE INDEX idx_companies_score ON companies(lead_score DESC);
CREATE INDEX idx_companies_location ON companies USING GIN (location);

CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_decision_maker ON contacts(is_decision_maker) WHERE is_decision_maker = true;

CREATE INDEX idx_scraped_data_company_type ON scraped_data(company_id, data_type);
CREATE INDEX idx_scraped_data_quality ON scraped_data(quality_score DESC);

CREATE INDEX idx_jobs_status_created ON scraping_jobs(status, created_at);
```

#### Row Level Security Policies
```sql
-- Enable RLS on all tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;

-- Create policies (for future multi-tenant support)
CREATE POLICY "Allow all for service role" ON companies
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow all for service role" ON contacts
    FOR ALL USING (auth.role() = 'service_role');
    
CREATE POLICY "Allow all for service role" ON scraped_data
    FOR ALL USING (auth.role() = 'service_role');
    
CREATE POLICY "Allow all for service role" ON scraping_jobs
    FOR ALL USING (auth.role() = 'service_role');
```

### Supabase Service Layer

#### CRUD Operations Wrapper
```python
# app/services/supabase_service.py
from typing import List, Dict, Any, Optional
from supabase import Client
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.schemas.contact import ContactCreate
from app.schemas.job import JobCreate, JobUpdate

class SupabaseService:
    def __init__(self, client: Client):
        self.client = client
    
    # Company operations
    async def create_company(self, company_data: CompanyCreate) -> Dict[str, Any]:
        """Create a new company record"""
        response = self.client.table('companies').insert(
            company_data.model_dump()
        ).execute()
        return response.data[0] if response.data else None
    
    async def get_companies(
        self, 
        limit: int = 20, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get companies with pagination and filters"""
        query = self.client.table('companies').select(
            "*, contacts(count)"
        ).range(offset, offset + limit - 1)
        
        if filters:
            for key, value in filters.items():
                if key == 'min_score':
                    query = query.gte('lead_score', value)
                elif key == 'industry':
                    query = query.eq('industry', value)
                elif key == 'size_category':
                    query = query.eq('size_category', value)
        
        response = query.execute()
        return response.data
    
    async def update_company_score(self, company_id: str, score: int) -> bool:
        """Update company lead score"""
        response = self.client.table('companies').update({
            'lead_score': score
        }).eq('id', company_id).execute()
        return len(response.data) > 0
    
    # Contact operations
    async def create_contacts(self, contacts_data: List[ContactCreate]) -> List[Dict[str, Any]]:
        """Bulk create contacts"""
        contacts_dict = [contact.model_dump() for contact in contacts_data]
        response = self.client.table('contacts').insert(contacts_dict).execute()
        return response.data
    
    async def get_company_contacts(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all contacts for a company"""
        response = self.client.table('contacts').select('*').eq(
            'company_id', company_id
        ).execute()
        return response.data
    
    # Job operations
    async def create_job(self, job_data: JobCreate) -> Dict[str, Any]:
        """Create a new scraping job"""
        response = self.client.table('scraping_jobs').insert(
            job_data.model_dump()
        ).execute()
        return response.data[0]
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        progress: int = None,
        results_count: int = None
    ) -> bool:
        """Update job status and progress"""
        update_data = {'status': status}
        if progress is not None:
            update_data['progress'] = progress
        if results_count is not None:
            update_data['results_count'] = results_count
        if status == 'completed':
            update_data['completed_at'] = 'now()'
        elif status == 'running':
            update_data['started_at'] = 'now()'
            
        response = self.client.table('scraping_jobs').update(
            update_data
        ).eq('id', job_id).execute()
        return len(response.data) > 0
    
    # Analytics queries
    async def get_lead_analytics(self) -> Dict[str, Any]:
        """Get analytics about leads"""
        # Total companies
        total_response = self.client.table('companies').select(
            'id', count='exact'
        ).execute()
        
        # Score distribution
        score_response = self.client.rpc('get_score_distribution').execute()
        
        # Industry breakdown
        industry_response = self.client.table('companies').select(
            'industry', count='exact'
        ).group_by('industry').execute()
        
        return {
            'total_companies': total_response.count,
            'score_distribution': score_response.data,
            'industry_breakdown': industry_response.data
        }
```

## 🗄️ 4. Data Storage & Management

### 4.1 Database Schema

```sql
-- Companies Table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    size_category company_size_enum,
    website VARCHAR(255),
    description TEXT,
    location JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    lead_score INTEGER DEFAULT 0,
    
    CONSTRAINT valid_score CHECK (lead_score >= 0 AND lead_score <= 100)
);

-- Contacts Table
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100),
    title VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    linkedin_url VARCHAR(255),
    is_decision_maker BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_email_per_company UNIQUE (company_id, email)
);

-- Scraped Data Table
CREATE TABLE scraped_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    source_url VARCHAR(500),
    data_type scrape_type_enum,
    raw_data JSONB,
    processed_data JSONB,
    scraped_at TIMESTAMP DEFAULT NOW(),
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    
    INDEX idx_company_data_type (company_id, data_type),
    INDEX idx_scraped_at (scraped_at)
);

-- Jobs Table
CREATE TABLE scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status job_status_enum DEFAULT 'pending',
    search_criteria JSONB,
    results_count INTEGER DEFAULT 0,
    errors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    INDEX idx_status_created (status, created_at)
);
```

### 4.2 Data Deduplication Strategy

```python
DEDUPLICATION_STRATEGY = {
    "company_matching": {
        "primary_key": "company_name + domain",
        "fuzzy_matching": {
            "algorithm": "levenshtein_distance",
            "threshold": 0.85,
            "fields": ["name", "website", "phone"]
        }
    },
    
    "contact_matching": {
        "primary_key": "email",
        "secondary_matching": "name + company_id",
        "merge_strategy": "keep_most_complete_record"
    }
}
```

## 🔌 5. API Endpoints

### 5.1 Core API Routes

#### Scraping Operations
```http
POST /api/v1/scrape/search
Content-Type: application/json

{
    "industry": "technology",
    "location": "San Francisco, CA",
    "company_size": "51-200",
    "max_results": 50
}

Response:
{
    "job_id": "uuid",
    "status": "initiated",
    "estimated_completion": "2025-06-03T10:30:00Z"
}
```

```http
GET /api/v1/scrape/status/{job_id}

Response:
{
    "status": "running",
    "progress": 45,
    "results_count": 23,
    "errors": [],
    "estimated_completion": "2025-06-03T10:25:00Z"
}
```

#### Lead Management
```http
GET /api/v1/leads?score_min=70&industry=technology&limit=20&offset=0

Response:
{
    "leads": [
        {
            "id": "uuid",
            "company_name": "TechCorp Inc",
            "industry": "Software Development",
            "lead_score": 85,
            "contact_count": 3,
            "location": {
                "city": "San Francisco",
                "state": "CA",
                "country": "US"
            },
            "created_at": "2025-06-03T09:15:00Z"
        }
    ],
    "total_count": 156,
    "pagination": {
        "has_next": true,
        "has_prev": false,
        "next_offset": 20
    }
}
```

```http
GET /api/v1/leads/{lead_id}

Response:
{
    "company": {
        "id": "uuid",
        "name": "TechCorp Inc",
        "industry": "Software Development",
        "size_category": "51-200",
        "website": "https://techcorp.com",
        "description": "Leading software development company...",
        "location": {...},
        "lead_score": 85
    },
    "contacts": [
        {
            "id": "uuid",
            "name": "John Doe",
            "title": "CEO",
            "email": "john@techcorp.com",
            "phone": "+1-555-123-4567",
            "linkedin_url": "linkedin.com/in/johndoe",
            "is_decision_maker": true
        }
    ],
    "intelligence": {
        "growth_signals": ["Recent hiring spree", "Series B funding"],
        "technology_stack": ["React", "Node.js", "AWS"],
        "pain_points": ["Scaling challenges", "Legacy system migration"]
    },
    "score_breakdown": {
        "contact_completeness": 22,
        "business_indicators": 28,
        "data_quality": 20,
        "engagement_potential": 15,
        "total": 85
    }
}
```

### 5.2 Export & Integration APIs

```http
GET /api/v1/export/csv?lead_ids=uuid1,uuid2&fields=name,email,phone,score

Response: CSV file download
```

```http
POST /api/v1/webhook/results
Content-Type: application/json

{
    "job_id": "uuid",
    "status": "completed",
    "results_summary": {
        "total_found": 45,
        "high_quality": 32,
        "medium_quality": 13,
        "processing_time": "00:05:23"
    }
}
```

## ⚡ 6. Performance & Scalability

### 6.1 Performance Requirements

| Metric | Target | Measurement |
|--------|---------|-------------|
| API Response Time | < 500ms | 95th percentile |
| Search Initiation | < 200ms | Average |
| Lead Retrieval | < 1000ms | With full data |
| Scraping Throughput | 100 companies/hour | Sustained rate |
| Success Rate | > 85% | Valid data extraction |
| Concurrent Users | 10 users | Without degradation |

### 6.2 Error Handling Strategy

```python
ERROR_HANDLING = {
    "scraping_failures": {
        "retry_strategy": "exponential_backoff",
        "max_retries": 3,
        "fallback_sources": "alternative_scrapers",
        "circuit_breaker": "after_5_consecutive_failures"
    },
    
    "api_errors": {
        "validation_errors": "400 with detailed field messages",
        "authentication_errors": "401 with clear auth requirements",
        "rate_limit_exceeded": "429 with retry_after header",
        "server_errors": "500 with unique error_id for tracking"
    },
    
    "data_quality_issues": {
        "invalid_emails": "flag_for_manual_review",
        "missing_contacts": "lower_lead_score_accordingly", 
        "blocked_websites": "mark_source_unavailable",
        "duplicate_data": "merge_with_existing_record"
    }
}
```

### 6.3 Monitoring & Logging

```python
MONITORING_METRICS = {
    "business_metrics": [
        "leads_generated_per_hour",
        "average_lead_score",
        "data_quality_percentage",
        "source_success_rates"
    ],
    
    "technical_metrics": [
        "api_response_times",
        "error_rates_by_endpoint",
        "database_query_performance",
        "scraping_job_queue_length"
    ],
    
    "alerting_thresholds": {
        "api_error_rate": "> 5%",
        "scraping_success_rate": "< 80%",
        "database_response_time": "> 2 seconds",
        "queue_backlog": "> 100 jobs"
    }
}
```

## 🎯 7. Minimum Viable Product (5-Hour Scope)

### Priority 1 (Hours 1-3): Core Features
- [x] Basic company search by industry + location
- [x] Google My Business scraping integration
- [x] Contact page scraping for emails/phones
- [x] Simple lead scoring (contact completeness only)
- [x] SQLite database with essential tables
- [x] REST API for search initiation and status check
- [x] Background job processing for scraping

### Priority 2 (Hour 4): Enhancement  
- [x] Data validation and basic cleaning
- [x] Simple deduplication by email/domain
- [x] Lead retrieval API with pagination
- [x] CSV export functionality
- [x] Basic error handling and logging

### Priority 3 (Hour 5): Polish
- [x] API documentation with examples
- [x] Docker containerization
- [x] Health check endpoints
- [x] Performance optimization
- [x] Demo data generation

### Post-MVP Enhancements (Future Iterations)
- [ ] Advanced lead scoring with multiple factors
- [ ] LinkedIn company data integration
- [ ] Technology stack detection
- [ ] Growth signals detection
- [ ] Advanced data enrichment
- [ ] CRM integration APIs
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance async API |
| Database | PostgreSQL/SQLite | Data persistence |
| Background Jobs | Celery + Redis | Async task processing |
| Web Scraping | BeautifulSoup + Requests | Data extraction |
| Data Validation | Pydantic | Schema validation |
| Authentication | JWT | API security |
| Documentation | OpenAPI/Swagger | Auto-generated docs |
| Containerization | Docker | Deployment |
| Testing | Pytest | Unit and integration tests |

## 📚 Dependencies

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Database
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9

# Web Scraping
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
fake-useragent==1.4.0

# Background Tasks
celery==5.3.4
redis==5.0.1

# Data Processing
pandas==2.1.3
phonenumbers==8.13.25
email-validator==2.1.0

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
```

This comprehensive backend system provides a solid foundation for a lead generation tool that can be built within the 5-hour constraint while remaining scalable for future enhancements.