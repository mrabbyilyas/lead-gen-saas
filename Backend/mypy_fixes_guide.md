# Guide untuk Fix 136 MyPy Errors yang Tersisa

## 1. Fix Pydantic Field Issues (PRIORITY HIGH)

### File: `app/models/api_schemas.py`

```python
# Error di line 392 dan 458: Field(..., int, int) format salah

# SEBELUM (salah):
field_name = Field(..., 10, 20)
field_name = Field(..., 100)

# SESUDAH (benar):
field_name = Field(..., ge=10, le=20)  # untuk range
field_name = Field(..., max_length=100)  # untuk max length
field_name = Field(..., gt=0)  # greater than
field_name = Field(..., lt=100)  # less than

# Contoh lengkap untuk field yang umum:
class SomeModel(BaseModel):
    age: int = Field(..., ge=0, le=150, description="Age in years")
    name: str = Field(..., min_length=1, max_length=100)
    score: float = Field(..., ge=0.0, le=100.0)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
```

## 2. Fix Type Annotations (QUICK WINS)

### Add missing type annotations:

```python
# File: app/services/data_processing/estimation.py
# Line 182, 469, 749:
errors: list[str] = []

# File: app/services/data_processing/enrichment.py
# Line 231, 709:
technologies: list[str] = []
errors: list[str] = []

# File: app/services/data_processing/pipeline.py
# Line 746:
errors: list[str] = []

# File: app/services/scraper/website_scraper.py
# Line 26, 290:
visited_urls: set[str] = set()
contact_sections: list[Tag] = []

# File: app/services/scraper/linkedin_scraper.py
# Line 146, 210:
companies: list[dict[str, Any]] = []
contacts: list[dict[str, Any]] = []

# File: app/services/scraper/google_scraper.py
# Line 84:
maps_results: list[dict[str, Any]] = []

# File: app/models/database.py - untuk semua Column Float:
data_quality_score: float = Column(Float)
lead_score: float = Column(Float)
contact_quality_score: float = Column(Float)
engagement_potential: float = Column(Float)
progress_percentage: float = Column(Float)
extraction_confidence: float = Column(Float)
data_completeness: float = Column(Float)
metric_value: float = Column(Float)
```

## 3. Fix Max Function Key Parameter Issues

### File: `app/services/data_processing/estimation.py` (lines 295, 312)
### File: `app/services/data_processing/enrichment.py` (line 562)

```python
# SEBELUM (error):
max_item = max(items, key=some_function)  # overloaded function error

# SESUDAH (fixed):
# Wrap dengan lambda:
max_item = max(items, key=lambda x: some_function(x))

# Atau buat function yang lebih explicit:
def get_score(item: Any) -> float:
    return some_function(item)

max_item = max(items, key=get_score)
```

## 4. Fix Boolean Assignment Issues

### File: `app/services/data_processing/estimation.py` (lines 334, 340)

```python
# SEBELUM (error):
bool_variable = 1  # int assigned to bool

# SESUDAH (fixed):
bool_variable = bool(1)  # convert to bool
# atau langsung:
bool_variable = True
```

## 5. Create Missing Validator Classes

### File: `app/services/data_processing/validators.py`

```python
# Tambah validator classes yang missing:

class URLValidator:
    @staticmethod
    def validate(url: str) -> bool:
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

class DomainValidator:
    @staticmethod
    def validate(domain: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|xn--[a-zA-Z0-9]+)$'
        return bool(re.match(pattern, domain))

class LinkedInURLValidator:
    @staticmethod
    def validate(url: str) -> bool:
        return 'linkedin.com' in url and URLValidator.validate(url)

class CompanyNameValidator:
    @staticmethod
    def validate(name: str) -> bool:
        return len(name.strip()) >= 2 and len(name) <= 255

class ContactNameValidator:
    @staticmethod
    def validate(name: str) -> bool:
        return len(name.strip()) >= 2 and len(name) <= 100
```

## 6. Fix Pipeline Return Type Issues

### File: `app/services/data_processing/pipeline.py`

```python
# Multiple errors tentang list vs dict type mismatch
# Lines 372, 451, 542, 608, 717, 778, 899

# SEBELUM (error):
def some_method(self) -> tuple[dict[str, Any], dict[str, Any]]:
    companies = [company1, company2]  # list
    contacts = [contact1, contact2]   # list
    return companies, contacts  # ERROR: returning lists instead of dicts

# SESUDAH (fixed) - change return type:
def some_method(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    companies = [company1, company2]
    contacts = [contact1, contact2]
    return companies, contacts

# Atau kalau memang harus return dict:
def some_method(self) -> tuple[dict[str, Any], dict[str, Any]]:
    companies_dict = {"data": companies, "count": len(companies)}
    contacts_dict = {"data": contacts, "count": len(contacts)}
    return companies_dict, contacts_dict
```

## 7. Add Missing Methods to Classes

### File: `app/services/data_processing/cleaning.py`

```python
class DataCleaner:
    # Add missing methods:
    def clean_company_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Clean and standardize company data"""
        cleaned = data.copy()
        # Add your cleaning logic here
        if 'name' in cleaned:
            cleaned['name'] = cleaned['name'].strip().title()
        return cleaned
    
    def clean_contact_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Clean and standardize contact data"""
        cleaned = data.copy()
        # Add your cleaning logic here
        if 'name' in cleaned:
            cleaned['name'] = cleaned['name'].strip().title()
        if 'email' in cleaned:
            cleaned['email'] = cleaned['email'].strip().lower()
        return cleaned
```

### File: `app/services/scraper/base_scraper.py`

```python
class BaseScraper:
    # Add missing methods:
    def set_rate_limiter(self, rate_limiter) -> None:
        """Set rate limiter for the scraper"""
        self.rate_limiter = rate_limiter
    
    def set_proxy_manager(self, proxy_manager) -> None:
        """Set proxy manager for the scraper"""
        self.proxy_manager = proxy_manager
    
    def set_progress_callback(self, callback) -> None:
        """Set progress callback function"""
        self.progress_callback = callback
    
    # Add missing _can_fetch method:
    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched"""
        try:
            from urllib.robotparser import RobotFileParser
            rp = RobotFileParser()
            rp.set_url(f"{url}/robots.txt")
            rp.read()
            return rp.can_fetch("*", url)
        except:
            return True  # Default to True if robots.txt check fails
    
    # Fix missing return statement (line 185):
    def some_method_with_missing_return(self) -> bool:  # Add proper return type
        # existing logic...
        return True  # Add return statement
```

## 8. Fix BeautifulSoup Union Type Issues

### File: `app/services/scraper/website_scraper.py`

```python
from bs4 import Tag, NavigableString

# SEBELUM (error):
for element in soup.find_all('a'):
    href = element.get('href')  # Error: NavigableString has no get
    text = element.text.strip() # Error: list has no strip

# SESUDAH (fixed):
for element in soup.find_all('a'):
    if isinstance(element, Tag):
        href = element.get('href')
        if href and isinstance(href, str):
            # process href
            pass
        
        # For text content:
        text_content = element.get_text(strip=True)
        if text_content:
            # process text
            pass
```

## 9. Fix SQLAlchemy Base Issues

### File: `app/models/database.py`

```python
# SEBELUM (error):
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Company(Base):  # Error: Invalid base class
    pass

# SESUDAH (fixed):
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = 'companies'
    # rest of the model...
```

## 10. Add Missing Enum Values

### File dengan ScrapingSource dan ScrapingStatus enums:

```python
class ScrapingSource(str, Enum):
    WEBSITE = "website"    # Add this
    LINKEDIN = "linkedin"
    GOOGLE = "google"
    DIRECTORY = "directory"

class ScrapingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"  # Add this
```

## 11. Fix Pydantic Model Fields

### Update your Create models to accept additional fields:

```python
# File: app/models/schemas.py or wherever these are defined

class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[int] = None
    source: Optional[str] = None  # Add this
    position: Optional[str] = None

class CompanyCreate(BaseModel):
    name: str
    website: Optional[HttpUrl] = None
    phone: Optional[str] = None      # Add this
    address: Optional[str] = None    # Add this
    source: Optional[str] = None     # Add this
    source_url: Optional[str] = None # Add this
    linkedin_url: Optional[str] = None # Add this
```

## 12. Fix Type Conversion Issues

### Handle HttpUrl conversions:

```python
# SEBELUM (error):
CompanyCreate(website="https://example.com")  # str vs HttpUrl

# SESUDAH (fixed):
from pydantic import HttpUrl

# Option 1: Convert in the calling code
from pydantic import HttpUrl
website_url = HttpUrl("https://example.com") if website else None
CompanyCreate(website=website_url)

# Option 2: Use validator in the model
class CompanyCreate(BaseModel):
    website: Optional[HttpUrl] = None
    
    @field_validator('website', mode='before')
    @classmethod
    def validate_website(cls, v):
        if isinstance(v, str):
            return HttpUrl(v)
        return v
```

## 13. Fix Missing Return Statements

### File: `app/services/supabase_service.py`

```python
# Find functions with missing return statements and add appropriate returns:

def get_companies(self, params: PaginationParams) -> list[dict]:
    try:
        # existing logic...
        return result
    except Exception as e:
        # handle error
        return []  # Add return statement

# Similar pattern for all functions with missing returns at lines:
# 117, 131, 141, 174, 189, 197, 205, 261, 360
```

## 14. Fix Missing Schema Classes

### File: `app/models/schemas.py` - add missing classes:

```python
class UserActivityCreate(BaseModel):
    user_id: int
    activity_type: str
    description: str

class UserActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    description: str
    created_at: datetime

class SystemMetricsCreate(BaseModel):
    metric_name: str
    metric_value: float
    timestamp: datetime

class SystemMetricsResponse(SystemMetricsCreate):
    id: int

class APIKeyCreate(BaseModel):
    name: str
    permissions: list[str]

class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[list[str]] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key: str
    permissions: list[str]
    created_at: datetime
```

## 15. Quick Fix Script untuk Automation

```python
#!/usr/bin/env python3
import re
import os

def fix_remaining_errors():
    """Apply common fixes automatically"""
    
    # Fix type annotations
    def add_type_annotations(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Common patterns
        patterns = [
            (r'(\s+errors) = \[\]', r'\1: list[str] = []'),
            (r'(\s+technologies) = \[\]', r'\1: list[str] = []'),
            (r'(\s+companies) = \[\]', r'\1: list[dict[str, Any]] = []'),
            (r'(\s+contacts) = \[\]', r'\1: list[dict[str, Any]] = []'),
            (r'(\s+visited_urls) = set\(\)', r'\1: set[str] = set()'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        with open(file_path, 'w') as f:
            f.write(content)
    
    # Apply to all Python files
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                add_type_annotations(file_path)

if __name__ == "__main__":
    fix_remaining_errors()
```

## Urutan Priority Fix:

1. **Pydantic Field issues** (api_schemas.py) - Blocking FastAPI
2. **Type annotations** - Quick wins
3. **Missing validator classes** - Import errors
4. **SQLAlchemy Base** - Database issues
5. **Missing enum values** - Attribute errors
6. **Pipeline return types** - Logic errors
7. **Missing methods** - Method errors
8. **BeautifulSoup types** - Web scraping errors

Fokus ke file-file ini dulu untuk impact maksimal!