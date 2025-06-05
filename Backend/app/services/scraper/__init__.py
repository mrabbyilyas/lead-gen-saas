"""Web scraping engine package.

This package contains the multi-source scraping system for lead generation,
including scrapers for Google My Business, LinkedIn, company websites,
and business directories.
"""

from .base_scraper import BaseScraper, ScrapingResult, ScrapingError
from .google_scraper import GoogleScraper
from .linkedin_scraper import LinkedInScraper
from .website_scraper import WebsiteScraper
from .scraper_factory import ScraperFactory, get_scraper_factory
from .rate_limiter import RateLimiter
from .proxy_manager import ProxyManager

__all__ = [
    "BaseScraper",
    "ScrapingResult",
    "ScrapingError",
    "GoogleScraper",
    "LinkedInScraper",
    "WebsiteScraper",
    "ScraperFactory",
    "get_scraper_factory",
    "RateLimiter",
    "ProxyManager",
]
