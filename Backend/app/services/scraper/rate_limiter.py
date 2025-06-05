"""Rate limiting utilities for web scraping."""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float = 1.0
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 5
    backoff_factor: float = 2.0
    max_backoff: float = 300.0  # 5 minutes


class RateLimiter:
    """Token bucket rate limiter with domain-specific limits."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._domain_limiters: Dict[str, 'DomainRateLimiter'] = {}
        self._global_limiter = DomainRateLimiter("global", self.config)

    def get_domain_limiter(self, url: str) -> 'DomainRateLimiter':
        """Get or create a rate limiter for a specific domain."""
        domain = urlparse(url).netloc.lower()
        
        if domain not in self._domain_limiters:
            self._domain_limiters[domain] = DomainRateLimiter(domain, self.config)
        
        return self._domain_limiters[domain]

    async def acquire(self, url: str) -> float:
        """Acquire permission to make a request. Returns delay in seconds."""
        domain_limiter = self.get_domain_limiter(url)
        
        # Check both domain-specific and global limits
        domain_delay = await domain_limiter.acquire()
        global_delay = await self._global_limiter.acquire()
        
        # Return the maximum delay required
        return max(domain_delay, global_delay)

    def reset_domain(self, url: str) -> None:
        """Reset rate limiting for a specific domain."""
        domain = urlparse(url).netloc.lower()
        if domain in self._domain_limiters:
            self._domain_limiters[domain].reset()

    def get_stats(self, url: str) -> Dict[str, any]:
        """Get rate limiting statistics for a domain."""
        domain_limiter = self.get_domain_limiter(url)
        return domain_limiter.get_stats()


class DomainRateLimiter:
    """Rate limiter for a specific domain using token bucket algorithm."""

    def __init__(self, domain: str, config: RateLimitConfig):
        self.domain = domain
        self.config = config
        
        # Token bucket for requests per second
        self.tokens = config.burst_size
        self.last_refill = time.time()
        
        # Sliding window for requests per minute/hour
        self.minute_requests = deque()
        self.hour_requests = deque()
        
        # Backoff tracking
        self.consecutive_failures = 0
        self.last_failure_time = 0
        
        # Statistics
        self.total_requests = 0
        self.total_delays = 0
        self.total_delay_time = 0.0

    async def acquire(self) -> float:
        """Acquire a token. Returns delay in seconds if rate limited."""
        current_time = time.time()
        
        # Check if we're in backoff period
        backoff_delay = self._check_backoff(current_time)
        if backoff_delay > 0:
            return backoff_delay
        
        # Refill tokens based on time elapsed
        self._refill_tokens(current_time)
        
        # Clean old requests from sliding windows
        self._clean_sliding_windows(current_time)
        
        # Check all rate limits
        delay = self._calculate_delay(current_time)
        
        if delay > 0:
            self.total_delays += 1
            self.total_delay_time += delay
            return delay
        
        # Consume a token and record the request
        self.tokens -= 1
        self.minute_requests.append(current_time)
        self.hour_requests.append(current_time)
        self.total_requests += 1
        
        return 0.0

    def _refill_tokens(self, current_time: float) -> None:
        """Refill tokens based on elapsed time."""
        elapsed = current_time - self.last_refill
        tokens_to_add = elapsed * self.config.requests_per_second
        
        self.tokens = min(
            self.config.burst_size,
            self.tokens + tokens_to_add
        )
        self.last_refill = current_time

    def _clean_sliding_windows(self, current_time: float) -> None:
        """Remove old requests from sliding windows."""
        # Remove requests older than 1 minute
        minute_cutoff = current_time - 60
        while self.minute_requests and self.minute_requests[0] < minute_cutoff:
            self.minute_requests.popleft()
        
        # Remove requests older than 1 hour
        hour_cutoff = current_time - 3600
        while self.hour_requests and self.hour_requests[0] < hour_cutoff:
            self.hour_requests.popleft()

    def _calculate_delay(self, current_time: float) -> float:
        """Calculate required delay based on all rate limits."""
        delays = []
        
        # Check tokens (requests per second)
        if self.tokens < 1:
            tokens_needed = 1 - self.tokens
            delay = tokens_needed / self.config.requests_per_second
            delays.append(delay)
        
        # Check requests per minute
        if len(self.minute_requests) >= self.config.requests_per_minute:
            oldest_request = self.minute_requests[0]
            delay = 60 - (current_time - oldest_request)
            if delay > 0:
                delays.append(delay)
        
        # Check requests per hour
        if len(self.hour_requests) >= self.config.requests_per_hour:
            oldest_request = self.hour_requests[0]
            delay = 3600 - (current_time - oldest_request)
            if delay > 0:
                delays.append(delay)
        
        return max(delays) if delays else 0.0

    def _check_backoff(self, current_time: float) -> float:
        """Check if we're in exponential backoff period."""
        if self.consecutive_failures == 0:
            return 0.0
        
        backoff_duration = min(
            self.config.backoff_factor ** self.consecutive_failures,
            self.config.max_backoff
        )
        
        elapsed_since_failure = current_time - self.last_failure_time
        remaining_backoff = backoff_duration - elapsed_since_failure
        
        return max(0.0, remaining_backoff)

    def record_failure(self) -> None:
        """Record a failure for exponential backoff."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

    def record_success(self) -> None:
        """Record a success, resetting failure count."""
        self.consecutive_failures = 0
        self.last_failure_time = 0

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.tokens = self.config.burst_size
        self.last_refill = time.time()
        self.minute_requests.clear()
        self.hour_requests.clear()
        self.consecutive_failures = 0
        self.last_failure_time = 0

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiting statistics."""
        current_time = time.time()
        self._clean_sliding_windows(current_time)
        
        return {
            "domain": self.domain,
            "tokens_available": self.tokens,
            "requests_last_minute": len(self.minute_requests),
            "requests_last_hour": len(self.hour_requests),
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "total_delays": self.total_delays,
            "average_delay": (
                self.total_delay_time / self.total_delays 
                if self.total_delays > 0 else 0.0
            ),
            "backoff_remaining": self._check_backoff(current_time)
        }


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts based on response patterns."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config)
        self._response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def record_response(self, url: str, response_time: float, success: bool) -> None:
        """Record response metrics for adaptive rate limiting."""
        domain = urlparse(url).netloc.lower()
        
        self._response_times[domain].append(response_time)
        self._error_rates[domain].append(0 if success else 1)
        
        domain_limiter = self.get_domain_limiter(url)
        
        if success:
            domain_limiter.record_success()
            # Gradually increase rate if consistently successful
            if len(self._error_rates[domain]) >= 10:
                recent_errors = sum(list(self._error_rates[domain])[-10:])
                if recent_errors == 0:
                    self._increase_rate(domain)
        else:
            domain_limiter.record_failure()
            # Decrease rate on errors
            self._decrease_rate(domain)

    def _increase_rate(self, domain: str) -> None:
        """Gradually increase request rate for well-behaving domains."""
        if domain in self._domain_limiters:
            limiter = self._domain_limiters[domain]
            current_rate = limiter.config.requests_per_second
            
            # Increase by 10%, but cap at reasonable limits
            new_rate = min(current_rate * 1.1, 5.0)
            limiter.config.requests_per_second = new_rate

    def _decrease_rate(self, domain: str) -> None:
        """Decrease request rate for problematic domains."""
        if domain in self._domain_limiters:
            limiter = self._domain_limiters[domain]
            current_rate = limiter.config.requests_per_second
            
            # Decrease by 50%, but maintain minimum rate
            new_rate = max(current_rate * 0.5, 0.1)
            limiter.config.requests_per_second = new_rate

    def get_adaptive_stats(self, url: str) -> Dict[str, any]:
        """Get adaptive rate limiting statistics."""
        domain = urlparse(url).netloc.lower()
        stats = self.get_stats(url)
        
        if domain in self._response_times:
            response_times = list(self._response_times[domain])
            error_rates = list(self._error_rates[domain])
            
            stats.update({
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "recent_error_rate": sum(error_rates[-10:]) / min(10, len(error_rates)) if error_rates else 0,
                "total_responses_tracked": len(response_times)
            })
        
        return stats