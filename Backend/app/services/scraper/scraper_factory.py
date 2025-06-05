"""Factory for creating and managing different types of scrapers."""

import logging
from typing import Dict, List, Optional, Type, Union
from enum import Enum

from .base_scraper import BaseScraper, ScrapingConfig
from .google_scraper import GoogleScraper
from .linkedin_scraper import LinkedInScraper
from .website_scraper import WebsiteScraper
from .rate_limiter import RateLimiter, AdaptiveRateLimiter
from .proxy_manager import ProxyManager


class ScraperType(Enum):
    """Available scraper types."""

    GOOGLE = "google"
    LINKEDIN = "linkedin"
    WEBSITE = "website"
    AUTO = "auto"  # Automatically choose best scraper


class ScraperFactory:
    """Factory for creating and managing scrapers."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._scrapers: Dict[ScraperType, Type[BaseScraper]] = {
            ScraperType.GOOGLE: GoogleScraper,
            ScraperType.LINKEDIN: LinkedInScraper,
            ScraperType.WEBSITE: WebsiteScraper,
        }
        self._rate_limiter: Optional[RateLimiter] = None
        self._proxy_manager: Optional[ProxyManager] = None
        self._default_config: Optional[ScrapingConfig] = None

    def set_rate_limiter(self, rate_limiter: RateLimiter) -> None:
        """Set the rate limiter for all scrapers."""
        self._rate_limiter = rate_limiter

    def set_proxy_manager(self, proxy_manager: ProxyManager) -> None:
        """Set the proxy manager for all scrapers."""
        self._proxy_manager = proxy_manager

    def set_default_config(self, config: ScrapingConfig) -> None:
        """Set default configuration for all scrapers."""
        self._default_config = config

    def create_scraper(
        self,
        scraper_type: Union[ScraperType, str],
        config: Optional[ScrapingConfig] = None,
    ) -> BaseScraper:
        """Create a scraper instance.

        Args:
            scraper_type: Type of scraper to create
            config: Optional configuration (uses default if not provided)

        Returns:
            Configured scraper instance

        Raises:
            ValueError: If scraper type is not supported
        """
        if isinstance(scraper_type, str):
            try:
                scraper_type = ScraperType(scraper_type.lower())
            except ValueError:
                raise ValueError(f"Unsupported scraper type: {scraper_type}")

        if scraper_type == ScraperType.AUTO:
            raise ValueError("Use auto_select_scraper() for automatic selection")

        if scraper_type not in self._scrapers:
            raise ValueError(f"Unsupported scraper type: {scraper_type}")

        # Use provided config or default
        scraper_config = config or self._default_config

        # Create scraper instance
        scraper_class = self._scrapers[scraper_type]
        scraper = scraper_class(scraper_config)

        # Set rate limiter and proxy manager if available
        if self._rate_limiter:
            scraper.set_rate_limiter(self._rate_limiter)

        if self._proxy_manager:
            scraper.set_proxy_manager(self._proxy_manager)

        self.logger.info(f"Created {scraper_type.value} scraper")
        return scraper

    def auto_select_scraper(
        self, query: str, config: Optional[ScrapingConfig] = None
    ) -> BaseScraper:
        """Automatically select the best scraper for a query.

        Args:
            query: Search query or URL
            config: Optional configuration

        Returns:
            Best scraper for the query
        """
        scraper_type = self._determine_best_scraper(query)
        return self.create_scraper(scraper_type, config)

    def create_multi_scraper(
        self,
        scraper_types: List[Union[ScraperType, str]],
        config: Optional[ScrapingConfig] = None,
    ) -> List[BaseScraper]:
        """Create multiple scrapers for parallel scraping.

        Args:
            scraper_types: List of scraper types to create
            config: Optional configuration

        Returns:
            List of configured scraper instances
        """
        scrapers = []

        for scraper_type in scraper_types:
            try:
                scraper = self.create_scraper(scraper_type, config)
                scrapers.append(scraper)
            except ValueError as e:
                self.logger.warning(f"Failed to create scraper {scraper_type}: {e}")

        return scrapers

    def _determine_best_scraper(self, query: str) -> ScraperType:
        """Determine the best scraper type for a query.

        Args:
            query: Search query or URL

        Returns:
            Best scraper type for the query
        """
        query_lower = query.lower().strip()

        # Check for LinkedIn URLs
        if "linkedin.com" in query_lower:
            return ScraperType.LINKEDIN

        # Check for Google-related queries
        google_indicators = ["google.com", "maps.google.com", "business.google.com"]
        if any(indicator in query_lower for indicator in google_indicators):
            return ScraperType.GOOGLE

        # Check if it's a URL (website scraping)
        if query_lower.startswith(("http://", "https://")) or "." in query:
            # If it contains a domain, use website scraper
            return ScraperType.WEBSITE

        # For general business searches, prefer Google
        business_keywords = [
            "company",
            "business",
            "corporation",
            "inc",
            "llc",
            "ltd",
            "restaurant",
            "store",
            "shop",
            "service",
            "agency",
        ]

        if any(keyword in query_lower for keyword in business_keywords):
            return ScraperType.GOOGLE

        # Default to Google for general queries
        return ScraperType.GOOGLE

    def get_supported_scrapers(self) -> List[ScraperType]:
        """Get list of supported scraper types.

        Returns:
            List of supported scraper types
        """
        return list(self._scrapers.keys())

    def get_scraper_info(self, scraper_type: Union[ScraperType, str]) -> Dict:
        """Get information about a scraper type.

        Args:
            scraper_type: Type of scraper

        Returns:
            Dictionary with scraper information

        Raises:
            ValueError: If scraper type is not supported
        """
        if isinstance(scraper_type, str):
            try:
                scraper_type = ScraperType(scraper_type.lower())
            except ValueError:
                raise ValueError(f"Unsupported scraper type: {scraper_type}")

        if scraper_type not in self._scrapers:
            raise ValueError(f"Unsupported scraper type: {scraper_type}")

        scraper_class = self._scrapers[scraper_type]

        return {
            "type": scraper_type.value,
            "class": scraper_class.__name__,
            "source": scraper_class(None).get_source().value,
            "description": scraper_class.__doc__ or "No description available",
        }

    def validate_scraper_config(self, config: ScrapingConfig) -> List[str]:
        """Validate scraper configuration.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if config.max_pages <= 0:
            errors.append("max_pages must be greater than 0")

        if config.max_pages > 100:
            errors.append("max_pages should not exceed 100 for performance reasons")

        if config.delay_between_requests < 0:
            errors.append("delay_between_requests cannot be negative")

        if config.delay_between_requests > 60:
            errors.append("delay_between_requests should not exceed 60 seconds")

        if config.timeout <= 0:
            errors.append("timeout must be greater than 0")

        if config.timeout > 300:
            errors.append("timeout should not exceed 300 seconds")

        if config.max_retries < 0:
            errors.append("max_retries cannot be negative")

        if config.max_retries > 10:
            errors.append("max_retries should not exceed 10")

        return errors

    @staticmethod
    def create_default_config(
        max_pages: int = 5,
        delay_between_requests: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        use_proxy: bool = False,
        respect_robots_txt: bool = True,
        user_agent: Optional[str] = None,
    ) -> ScrapingConfig:
        """Create a default scraping configuration.

        Args:
            max_pages: Maximum pages to scrape
            delay_between_requests: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            use_proxy: Whether to use proxy
            respect_robots_txt: Whether to respect robots.txt
            user_agent: Custom user agent string

        Returns:
            Default scraping configuration
        """
        return ScrapingConfig(
            max_pages=max_pages,
            delay_between_requests=delay_between_requests,
            timeout=timeout,
            max_retries=max_retries,
            use_proxy=use_proxy,
            respect_robots_txt=respect_robots_txt,
            user_agent=user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

    @staticmethod
    def create_rate_limiter(
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        adaptive: bool = False,
    ) -> Union[RateLimiter, AdaptiveRateLimiter]:
        """Create a rate limiter instance.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            adaptive: Whether to use adaptive rate limiting

        Returns:
            Configured rate limiter
        """
        from .rate_limiter import RateLimitConfig

        config = RateLimitConfig(
            requests_per_minute=requests_per_minute, requests_per_hour=requests_per_hour
        )

        if adaptive:
            return AdaptiveRateLimiter(config=config)
        else:
            return RateLimiter(config=config)

    @staticmethod
    def create_proxy_manager(
        proxy_list: Optional[List[str]] = None, rotation_strategy: str = "round_robin"
    ) -> ProxyManager:
        """Create a proxy manager instance.

        Args:
            proxy_list: List of proxy URLs
            rotation_strategy: Proxy rotation strategy

        Returns:
            Configured proxy manager
        """
        # Convert proxy URLs to ProxyConfig objects
        from .proxy_manager import ProxyConfig, ProxyType

        proxy_configs = []
        for proxy_url in proxy_list or []:
            # Parse proxy URL and create ProxyConfig
            # For now, create basic HTTP proxy configs
            parts = proxy_url.split(":")
            if len(parts) >= 2:
                proxy_configs.append(
                    ProxyConfig(
                        host=parts[0], port=int(parts[1]), proxy_type=ProxyType.HTTP
                    )
                )

        return ProxyManager(proxy_configs=proxy_configs)


# Global factory instance
scraper_factory = ScraperFactory()


# Convenience functions
def create_scraper(
    scraper_type: Union[ScraperType, str], config: Optional[ScrapingConfig] = None
) -> BaseScraper:
    """Convenience function to create a scraper."""
    return scraper_factory.create_scraper(scraper_type, config)


def auto_select_scraper(
    query: str, config: Optional[ScrapingConfig] = None
) -> BaseScraper:
    """Convenience function to auto-select a scraper."""
    return scraper_factory.auto_select_scraper(query, config)


def get_supported_scrapers() -> List[ScraperType]:
    """Convenience function to get supported scrapers."""
    return scraper_factory.get_supported_scrapers()


def get_scraper_factory() -> ScraperFactory:
    """Get the global scraper factory instance."""
    return scraper_factory
