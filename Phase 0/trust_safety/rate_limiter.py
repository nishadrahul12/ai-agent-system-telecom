"""
Rate Limiter: Prevent abuse through rate limiting.

Implements:
    - Token bucket algorithm
    - Per-user rate limits
    - Automatic window reset
    - Metrics tracking

Usage:
    limiter = RateLimiter(max_requests=100, window_seconds=60)
    if limiter.check_limit(user_id="user_123"):
        process_request()
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Default rate limiting
DEFAULT_MAX_REQUESTS = 100
DEFAULT_WINDOW_SECONDS = 60


class RateLimiter:
    """
    Rate limiting using token bucket algorithm.
    
    Attributes:
        max_requests (int): Max requests per window
        window_seconds (int): Time window in seconds
        _buckets (dict): Request counters per user
        _reset_time (dict): Window reset time per user
    """
    
    def __init__(
        self,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        """
        Initialize rate limiter.
        
        Args:
            max_requests (int): Max requests allowed. Defaults to 100
            window_seconds (int): Time window in seconds. Defaults to 60
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, int] = defaultdict(int)
        self._reset_time: Dict[str, datetime] = {}
        
        logger.info(
            f"RateLimiter initialized ({max_requests} req/{window_seconds}s)"
        )
    
    def check_limit(self, identifier: str = "global") -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            identifier (str): User/client identifier. Defaults to "global"
            
        Returns:
            bool: True if request allowed, False if rate limited
            
        Example:
            >>> limiter = RateLimiter(max_requests=10, window_seconds=60)
            >>> if limiter.check_limit(user_id):
            ...     process_request()
        """
        now = datetime.utcnow()
        
        # Initialize or reset bucket if needed
        if identifier not in self._reset_time:
            self._reset_time[identifier] = now + timedelta(seconds=self.window_seconds)
            self._buckets[identifier] = 0
        
        # Reset bucket if window expired
        if now > self._reset_time[identifier]:
            self._reset_time[identifier] = now + timedelta(seconds=self.window_seconds)
            self._buckets[identifier] = 0
        
        # Check limit
        if self._buckets[identifier] < self.max_requests:
            self._buckets[identifier] += 1
            return True
        
        logger.warning(f"Rate limit exceeded for {identifier}")
        return False
    
    def get_status(self, identifier: str = "global") -> Dict[str, any]:
        """
        Get rate limit status for identifier.
        
        Args:
            identifier (str): User/client identifier
            
        Returns:
            Dict[str, any]: Status containing:
                - requests_used (int): Requests used in current window
                - requests_remaining (int): Requests available
                - reset_time (str): ISO format reset time
        """
        if identifier not in self._buckets:
            return {
                "requests_used": 0,
                "requests_remaining": self.max_requests,
                "reset_time": (
                    datetime.utcnow() + timedelta(seconds=self.window_seconds)
                ).isoformat(),
            }
        
        requests_used = self._buckets[identifier]
        requests_remaining = max(0, self.max_requests - requests_used)
        
        return {
            "requests_used": requests_used,
            "requests_remaining": requests_remaining,
            "reset_time": self._reset_time[identifier].isoformat(),
        }
    
    def get_all_status(self) -> Dict[str, Dict]:
        """
        Get rate limit status for all identifiers.
        
        Returns:
            Dict[str, Dict]: Status for each identifier
        """
        return {
            identifier: self.get_status(identifier)
            for identifier in self._buckets.keys()
        }
    
    def reset_limit(self, identifier: str = "global") -> bool:
        """
        Reset rate limit for identifier.
        
        Args:
            identifier (str): User/client identifier
            
        Returns:
            bool: True if reset
        """
        if identifier in self._buckets:
            self._buckets[identifier] = 0
            self._reset_time[identifier] = (
                datetime.utcnow() + timedelta(seconds=self.window_seconds)
            )
            logger.info(f"Rate limit reset for {identifier}")
            return True
        
        return False
    
    def clear_all(self) -> None:
        """Clear all rate limit data."""
        self._buckets.clear()
        self._reset_time.clear()
        logger.info("All rate limits cleared")
