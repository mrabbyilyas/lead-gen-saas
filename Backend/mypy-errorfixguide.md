# Final MyPy Fixes Guide - 20 Errors

## Error Summary:
- **3 Type annotation errors** (subscriptable types)
- **17 "Returning Any" errors** (type return mismatches)

## Files with Errors:
1. `app\services\scraper\rate_limiter.py` - 2 errors
2. `app\services\data_processing\deduplication.py` - 5 errors
3. `app\services\data_processing\cleaning.py` - 3 errors
4. `app\services\data_processing\estimation.py` - 4 errors
5. `app\services\data_processing\enrichment.py` - 2 errors
6. `app\services\scraper\base_scraper.py` - 2 errors
7. `app\services\scraper\website_scraper.py` - 1 error
8. `app\services\background_jobs\job_manager.py` - 1 error

---

## Fix 1: Type Annotation Issues (3 errors)

### Problem: Non-subscriptable types

#### `app/services/scraper/rate_limiter.py` (Lines 74-75)
```python
# Wrong - Python < 3.9 style
def __init__(self):
    self.requests: deque[float] = deque()  # Error!
    self.tokens: deque[float] = deque()    # Error!
```

#### `app/services/scraper/website_scraper.py` (Line 27)
```python
# Wrong - Python < 3.9 style  
visited_urls: set[str] = set()  # Error!
```

### Solution: Use typing imports

```python
# Fix for rate_limiter.py - Add imports at top
from typing import Deque
from collections import deque

# Fix lines 74-75
def __init__(self):
    self.requests: Deque[float] = deque()
    self.tokens: Deque[float] = deque()

# Fix for website_scraper.py - Add import at top
from typing import Set

# Fix line 27
visited_urls: Set[str] = set()
```

### Alternative Solution (Python 3.9+)
If you're using Python 3.9+, add this import:
```python
from __future__ import annotations

# Then the original syntax works:
self.requests: deque[float] = deque()
visited_urls: set[str] = set()
```

---

## Fix 2: "Returning Any" Errors (17 errors)

### Problem: Functions return `Any` instead of declared types

These errors occur when a function is declared to return a specific type but actually returns `Any`. This usually happens with:
- Dictionary access that might return `Any`
- JSON parsing results
- External API responses
- Untyped function calls

### Solutions by File:

#### `app/services/data_processing/deduplication.py` (5 errors)

```python
# Lines 679, 826, 844, 859, 865 - Add explicit type casting

# Line 679: Returning Any from function declared to return "str"
def some_function(...) -> str:
    result = some_dict.get("key")  # This returns Any
    return str(result) if result is not None else ""  # Cast to str

# Line 826 & 844: Returning Any from function declared to return "DeduplicationResult"
def deduplicate(...) -> DeduplicationResult:
    result = external_function()  # Returns Any
    # Cast or validate the result
    if isinstance(result, dict):
        return DeduplicationResult(**result)
    return DeduplicationResult()  # or appropriate default

# Lines 859 & 865: Returning Any from function declared to return "List[MatchResult]"
def find_matches(...) -> List[MatchResult]:
    results = some_api_call()  # Returns Any
    # Cast to proper type
    if isinstance(results, list):
        return [MatchResult(**item) if isinstance(item, dict) else item for item in results]
    return []
```

#### `app/services/data_processing/cleaning.py` (3 errors)

```python
# Lines 276, 282, 288 - Returning Any from function declared to return "List[str]"

# Fix pattern:
def clean_data(...) -> List[str]:
    result = process_data()  # Returns Any
    
    # Ensure we return List[str]
    if isinstance(result, list):
        return [str(item) for item in result]
    elif isinstance(result, str):
        return [result]
    else:
        return []  # Safe default
```

#### `app/services/data_processing/estimation.py` (4 errors)

```python
# Lines 278, 295, 312 - Returning Any from function declared to return "Optional[CompanySize]"
def estimate_company_size(...) -> Optional[CompanySize]:
    raw_result = api_call()  # Returns Any
    
    # Type-safe conversion
    if raw_result is None:
        return None
    
    if isinstance(raw_result, str):
        try:
            return CompanySize(raw_result)
        except ValueError:
            return None
    elif isinstance(raw_result, dict) and "size" in raw_result:
        try:
            return CompanySize(raw_result["size"])
        except (ValueError, KeyError):
            return None
    
    return None

# Line 668 - Returning Any from function declared to return "RevenueRange"
def estimate_revenue(...) -> RevenueRange:
    result = calculate_revenue()  # Returns Any
    
    # Ensure we return RevenueRange
    if isinstance(result, dict):
        return RevenueRange(**result)
    elif isinstance(result, str):
        return RevenueRange(result)
    else:
        return RevenueRange()  # Default constructor
```

#### `app/services/data_processing/enrichment.py` (2 errors)

```python
# Lines 562, 774 - Returning Any from function declared to return "Optional[str]"
def enrich_data(...) -> Optional[str]:
    result = external_service.get_data()  # Returns Any
    
    # Safe string conversion
    if result is None:
        return None
    
    return str(result) if result else None
```

#### `app/services/scraper/base_scraper.py` (2 errors)

```python
# Lines 238, 244 - Returning Any from function declared to return "str"
def extract_text(...) -> str:
    element = soup.find("div")  # Returns Any (from BeautifulSoup)
    
    # Safe string extraction
    if element and hasattr(element, 'get_text'):
        return element.get_text(strip=True)
    elif element and hasattr(element, 'text'):
        return str(element.text)
    else:
        return ""  # Safe default
```

#### `app/services/background_jobs/job_manager.py` (1 error)

```python
# Line 188 - Returning Any from function declared to return "Dict[str, Any]"
def get_job_info(...) -> Dict[str, Any]:
    result = celery_task.info  # Returns Any
    
    # Ensure we return Dict[str, Any]
    if isinstance(result, dict):
        return result
    else:
        return {}  # Safe default
```

---

## Complete File-by-File Fixes

### 1. `app/services/scraper/rate_limiter.py`

```python
# Add these imports at the top
from typing import Deque
from collections import deque

# Fix lines 74-75
class RateLimiter:
    def __init__(self):
        self.requests: Deque[float] = deque()
        self.tokens: Deque[float] = deque()
```

### 2. `app/services/scraper/website_scraper.py`

```python
# Add this import at the top
from typing import Set

# Fix line 27
class WebsiteScraper:
    def __init__(self):
        self.visited_urls: Set[str] = set()
```

### 3. General Pattern for "Returning Any" Fixes

```python
# Before (causes error):
def my_function() -> str:
    result = some_dict.get("key")  # Returns Any
    return result  # Error: Returning Any from function declared to return "str"

# After (fixed):
def my_function() -> str:
    result = some_dict.get("key")  # Returns Any
    return str(result) if result is not None else ""  # Explicit conversion

# For Optional returns:
def my_function() -> Optional[str]:
    result = some_dict.get("key")  # Returns Any
    return str(result) if result is not None else None

# For List returns:
def my_function() -> List[str]:
    result = some_api_call()  # Returns Any
    if isinstance(result, list):
        return [str(item) for item in result]
    return []

# For Dict returns:
def my_function() -> Dict[str, Any]:
    result = some_call()  # Returns Any
    return dict(result) if isinstance(result, dict) else {}
```

---

## Quick Action Plan:

### Step 1: Fix Type Annotations (3 errors)
```python
# Add to imports in respective files:
from typing import Deque, Set
from collections import deque

# Update type hints:
# deque[T] → Deque[T]
# set[T] → Set[T]
```

### Step 2: Fix "Returning Any" Errors (17 errors)
For each error, add explicit type conversion:

```python
# Pattern 1: String returns
return str(result) if result is not None else ""

# Pattern 2: Optional returns  
return str(result) if result is not None else None

# Pattern 3: List returns
return [str(item) for item in result] if isinstance(result, list) else []

# Pattern 4: Dict returns
return dict(result) if isinstance(result, dict) else {}
```

### Step 3: Verify
```bash
mypy .
```

After these fixes, you should have **0 mypy errors**!

---

## Alternative: Suppress Specific Errors (Quick Fix)

If you want a quick temporary fix while working on proper typing:

```python
# Add # type: ignore comments to suppress specific errors:

result = some_call()
return result  # type: ignore[no-any-return]
```

But the proper fixes above are recommended for production code.