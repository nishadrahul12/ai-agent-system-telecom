"""
Trust & Safety Module: Input validation, PII detection, rate limiting.

Provides:
    - Input validation and sanitization
    - PII (Personally Identifiable Information) detection
    - Rate limiting and throttling
    - Security boundary enforcement

Usage:
    safety = SafetyGuard()
    if safety.validate_input({"data": "..."}):
        process()
"""

__version__ = "0.1.0"

from trust_safety.safety_guard import SafetyGuard
from trust_safety.privacy_checker import PrivacyChecker
from trust_safety.rate_limiter import RateLimiter

__all__ = ["SafetyGuard", "PrivacyChecker", "RateLimiter"]
