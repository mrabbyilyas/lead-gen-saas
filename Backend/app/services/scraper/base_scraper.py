"""Base scraper class and common scraping utilities."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)

from app.models.schemas import CompanyCreate, ContactCreate


class ScrapingStatus(str, Enum):
    """Scraping operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"


class ScrapingSource(str, Enum):
    """Supported scraping sources."""
    GOOGLE_MY_BUSINESS = "google_my_business"
    LINKEDIN = "linkedin"
    COMPANY_WEBSITE = "company_website"
    BUSINESS_DIRECTORY = "business_directory"
    YELLOW_PAGES = "yellow_pages"
    YELP = "yelp"


@dataclass
class ScrapingConfig:
    """Configuration for scraping operations."""
    max_pages: int = 10
    delay_between_requests: float = 1.0
    timeout: int = 30
    max_retries: int = 3
    use_proxy: bool = False
    proxy_rotation: bool = True
    respect_robots_txt: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    javascript_enabled: bool = False
    screenshot_on_error: bool = False
    save_html: bool = False


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    source: ScrapingSource
    status: ScrapingStatus
    companies: List[CompanyCreate] = field(default_factory=list)
    contacts: List[ContactCreate] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scraped_urls: Set[str] = field(default_factory=set)
    total_pages_scraped: int = 0
    total_records_found: int = 0
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def add_company(self, company: CompanyCreate) -> None:
        """Add a company to the results."""
        self.companies.append(company)
        self.total_records_found += 1

    def add_contact(self, contact: ContactCreate) -> None:
        """Add a contact to the results."""
        self.contacts.append(contact)
        self.total_records_found += 1

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logging.error(f"Scraping error: {error}")

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        logging.warning(f"Scraping warning: {warning}")


class ScrapingError(Exception):
    """Base exception for scraping operations."""
    
    def __init__(self, message: str, source: Optional[ScrapingSource] = None, 
                 url: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.source = source
        self.url = url
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class RateLimitError(ScrapingError):
    """Exception raised when rate limit is exceeded."""
    pass


class BlockedError(ScrapingError):
    """Exception raised when scraper is blocked."""
    pass


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.driver: Optional[webdriver.Chrome] = None
        self._setup_session()

    def _setup_session(self) -> None:
        """Setup the requests session with headers and configuration."""
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        headers.update(self.config.headers)
        self.session.headers.update(headers)
        
        if self.config.cookies:
            self.session.cookies.update(self.config.cookies)

    def _get_driver(self) -> webdriver.Chrome:
        """Get or create a Chrome WebDriver instance."""
        if self.driver is None:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"--user-agent={self.config.user_agent}")
            
            if self.config.use_proxy:
                # Proxy configuration would be added here
                pass
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.timeout)
        
        return self.driver

    def _close_driver(self) -> None:
        """Close the WebDriver instance."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """Make an HTTP request with error handling and retries."""
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                
                if response.status_code == 429:
                    raise RateLimitError(f"Rate limit exceeded for {url}", url=url)
                
                if response.status_code == 403:
                    raise BlockedError(f"Access blocked for {url}", url=url)
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries:
                    raise ScrapingError(f"Request failed after {self.config.max_retries} retries: {e}", url=url)
                
                wait_time = (attempt + 1) * self.config.delay_between_requests
                self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)

    def _parse_html(self, html: str, url: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            self.logger.warning(f"Failed to parse HTML with lxml, falling back to html.parser: {e}")
            return BeautifulSoup(html, 'html.parser')

    def _extract_text(self, element, default: str = "") -> str:
        """Safely extract text from a BeautifulSoup element."""
        if element:
            return element.get_text(strip=True)
        return default

    def _extract_attribute(self, element, attribute: str, default: str = "") -> str:
        """Safely extract an attribute from a BeautifulSoup element."""
        if element and element.has_attr(attribute):
            return element[attribute]
        return default

    def _clean_url(self, url: str, base_url: str = "") -> str:
        """Clean and normalize a URL."""
        if not url:
            return ""
        
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/") and base_url:
            url = urljoin(base_url, url)
        elif not url.startswith(("http://", "https://")):
            if base_url:
                url = urljoin(base_url, url)
            else:
                url = "https://" + url
        
        return url

    def _clean_phone(self, phone: str) -> str:
        """Clean and format phone number."""
        if not phone:
            return ""
        
        # Remove common phone number formatting
        import re
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Basic phone number validation
        if len(phone) >= 10:
            return phone
        
        return ""

    def _clean_email(self, email: str) -> str:
        """Clean and validate email address."""
        if not email:
            return ""
        
        email = email.strip().lower()
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email
        
        return ""

    def _respect_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt."""
        if not self.config.respect_robots_txt:
            return True
        
        try:
            from urllib.robotparser import RobotFileParser
            
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(self.config.user_agent, url)
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True

    def _wait_between_requests(self) -> None:
        """Wait between requests to respect rate limits."""
        if self.config.delay_between_requests > 0:
            time.sleep(self.config.delay_between_requests)

    @abstractmethod
    def get_source(self) -> ScrapingSource:
        """Get the scraping source identifier."""
        pass

    @abstractmethod
    async def scrape(self, query: str, **kwargs) -> ScrapingResult:
        """Perform the scraping operation."""
        pass

    @abstractmethod
    def validate_query(self, query: str) -> bool:
        """Validate if the query is suitable for this scraper."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self._close_driver()
        if hasattr(self.session, 'close'):
            self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self._close_driver()
        if hasattr(self.session, 'close'):
            self.session.close()