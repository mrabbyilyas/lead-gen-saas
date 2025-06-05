"""Proxy management for web scraping."""

import asyncio
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlparse

import requests


class ProxyType(str, Enum):
    """Types of proxy protocols."""

    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyStatus(str, Enum):
    """Proxy status states."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    TESTING = "testing"


@dataclass
class ProxyConfig:
    """Configuration for a proxy server."""

    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    max_concurrent_requests: int = 5
    timeout: int = 30
    test_url: str = "http://httpbin.org/ip"

    @property
    def url(self) -> str:
        """Get the proxy URL."""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"

    @property
    def dict(self) -> Dict[str, str]:
        """Get proxy configuration as dictionary for requests."""
        return {"http": self.url, "https": self.url}


@dataclass
class ProxyStats:
    """Statistics for a proxy server."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    rate_limited_requests: int = 0
    total_response_time: float = 0.0
    last_used: Optional[float] = None
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests


class ProxyServer:
    """Represents a proxy server with its configuration and statistics."""

    def __init__(self, config: ProxyConfig):
        self.config = config
        self.status = ProxyStatus.INACTIVE
        self.stats = ProxyStats()
        self.active_requests = 0
        self.last_health_check: float = 0.0
        self.health_check_interval = 300  # 5 minutes

    async def test_connection(self) -> bool:
        """Test if the proxy is working."""
        try:
            start_time = time.time()

            response = requests.get(
                self.config.test_url,
                proxies=self.config.dict,
                timeout=self.config.timeout,
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                self.status = ProxyStatus.ACTIVE
                self.stats.successful_requests += 1
                self.stats.total_response_time += response_time
                self.stats.last_success = time.time()
                self.stats.consecutive_failures = 0
                return True
            else:
                self._record_failure()
                return False

        except Exception:
            self._record_failure()
            return False
        finally:
            self.stats.total_requests += 1
            self.stats.last_used = time.time()

    def _record_failure(self) -> None:
        """Record a proxy failure."""
        self.stats.failed_requests += 1
        self.stats.last_failure = time.time()
        self.stats.consecutive_failures += 1

        if self.stats.consecutive_failures >= 3:
            self.status = ProxyStatus.ERROR
        elif self.stats.consecutive_failures >= 5:
            self.status = ProxyStatus.BLOCKED

    def record_request(
        self,
        success: bool,
        response_time: float = 0.0,
        blocked: bool = False,
        rate_limited: bool = False,
    ) -> None:
        """Record the result of a request made through this proxy."""
        self.stats.total_requests += 1
        self.stats.last_used = time.time()

        if success:
            self.stats.successful_requests += 1
            self.stats.total_response_time += response_time
            self.stats.last_success = time.time()
            self.stats.consecutive_failures = 0
            if self.status == ProxyStatus.ERROR:
                self.status = ProxyStatus.ACTIVE
        else:
            if blocked:
                self.stats.blocked_requests += 1
                self.status = ProxyStatus.BLOCKED
            elif rate_limited:
                self.stats.rate_limited_requests += 1
                self.status = ProxyStatus.RATE_LIMITED
            else:
                self._record_failure()

    def can_handle_request(self) -> bool:
        """Check if proxy can handle another request."""
        return (
            self.status == ProxyStatus.ACTIVE
            and self.active_requests < self.config.max_concurrent_requests
        )

    def needs_health_check(self) -> bool:
        """Check if proxy needs a health check."""
        return (
            time.time() - self.last_health_check > self.health_check_interval
            or self.status in [ProxyStatus.ERROR, ProxyStatus.BLOCKED]
        )


class ProxyManager:
    """Manages a pool of proxy servers with rotation and health checking."""

    def __init__(self, proxy_configs: List[ProxyConfig]):
        self.proxies = [ProxyServer(config) for config in proxy_configs]
        self.rotation_index = 0
        self.domain_proxy_mapping: Dict[str, ProxyServer] = {}
        self.blocked_domains: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize all proxies by testing their connections."""
        tasks = [proxy.test_connection() for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        active_count = sum(1 for result in results if result is True)
        print(f"Initialized {active_count}/{len(self.proxies)} proxies successfully")

    def get_proxy_for_domain(self, url: str) -> Optional[ProxyServer]:
        """Get the best proxy for a specific domain."""
        domain = urlparse(url).netloc.lower()

        # Check if domain is blocked
        if domain in self.blocked_domains:
            return None

        # Return existing proxy for domain if it's still good
        if domain in self.domain_proxy_mapping:
            proxy = self.domain_proxy_mapping[domain]
            if proxy.can_handle_request():
                return proxy

        # Find the best available proxy
        available_proxies = [
            proxy for proxy in self.proxies if proxy.can_handle_request()
        ]

        if not available_proxies:
            return None

        # Sort by success rate and response time
        available_proxies.sort(
            key=lambda p: (-p.stats.success_rate, p.stats.average_response_time)
        )

        best_proxy = available_proxies[0]
        self.domain_proxy_mapping[domain] = best_proxy

        return best_proxy

    def get_next_proxy(self) -> Optional[ProxyServer]:
        """Get the next proxy using round-robin rotation."""
        available_proxies = [
            proxy for proxy in self.proxies if proxy.can_handle_request()
        ]

        if not available_proxies:
            return None

        # Round-robin selection
        proxy = available_proxies[self.rotation_index % len(available_proxies)]
        self.rotation_index += 1

        return proxy

    def get_random_proxy(self) -> Optional[ProxyServer]:
        """Get a random available proxy."""
        available_proxies = [
            proxy for proxy in self.proxies if proxy.can_handle_request()
        ]

        if not available_proxies:
            return None

        return random.choice(available_proxies)

    def record_request_result(
        self,
        proxy: ProxyServer,
        url: str,
        success: bool,
        response_time: float = 0.0,
        blocked: bool = False,
        rate_limited: bool = False,
    ) -> None:
        """Record the result of a request made through a proxy."""
        proxy.record_request(success, response_time, blocked, rate_limited)

        if blocked:
            domain = urlparse(url).netloc.lower()
            self.blocked_domains.add(domain)
            # Remove domain mapping if proxy is blocked for this domain
            if domain in self.domain_proxy_mapping:
                del self.domain_proxy_mapping[domain]

    async def health_check_all(self) -> None:
        """Perform health checks on all proxies that need it."""
        proxies_to_check = [
            proxy for proxy in self.proxies if proxy.needs_health_check()
        ]

        if proxies_to_check:
            tasks = [proxy.test_connection() for proxy in proxies_to_check]
            await asyncio.gather(*tasks, return_exceptions=True)

            for proxy in proxies_to_check:
                proxy.last_health_check = time.time()

    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get statistics for all proxies."""
        active_proxies = [p for p in self.proxies if p.status == ProxyStatus.ACTIVE]

        return {
            "total_proxies": len(self.proxies),
            "active_proxies": len(active_proxies),
            "blocked_domains": len(self.blocked_domains),
            "average_success_rate": (
                sum(p.stats.success_rate for p in active_proxies) / len(active_proxies)
                if active_proxies
                else 0
            ),
            "proxy_details": [
                {
                    "host": proxy.config.host,
                    "port": proxy.config.port,
                    "status": proxy.status.value,
                    "success_rate": proxy.stats.success_rate,
                    "total_requests": proxy.stats.total_requests,
                    "average_response_time": proxy.stats.average_response_time,
                    "consecutive_failures": proxy.stats.consecutive_failures,
                }
                for proxy in self.proxies
            ],
        }

    def remove_proxy(self, host: str, port: int) -> bool:
        """Remove a proxy from the pool."""
        for i, proxy in enumerate(self.proxies):
            if proxy.config.host == host and proxy.config.port == port:
                del self.proxies[i]
                # Clean up domain mappings
                domains_to_remove = [
                    domain
                    for domain, mapped_proxy in self.domain_proxy_mapping.items()
                    if mapped_proxy == proxy
                ]
                for domain in domains_to_remove:
                    del self.domain_proxy_mapping[domain]
                return True
        return False

    def add_proxy(self, config: ProxyConfig) -> None:
        """Add a new proxy to the pool."""
        proxy = ProxyServer(config)
        self.proxies.append(proxy)

    def clear_blocked_domains(self) -> None:
        """Clear the list of blocked domains."""
        self.blocked_domains.clear()
        self.domain_proxy_mapping.clear()
