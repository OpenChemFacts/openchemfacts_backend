"""
Security utilities for OpenChemFacts Backend API.

This module provides:
- Rate limiting configuration
- API key validation (for Phase 2)
"""
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Rate limiting configuration from environment variables
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PLOT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PLOT_PER_MINUTE", "10"))
RATE_LIMIT_HEALTH_PER_MINUTE = int(os.getenv("RATE_LIMIT_HEALTH_PER_MINUTE", "120"))

# Create rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on client IP address.
    
    Considers X-Forwarded-For header for requests behind proxies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        IP address string for rate limiting
    """
    # Check for forwarded IP (when behind proxy/load balancer)
    if "X-Forwarded-For" in request.headers:
        # Take the first IP in the chain
        forwarded_ips = request.headers["X-Forwarded-For"].split(",")
        return forwarded_ips[0].strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


# Update limiter key function
limiter.key_func = get_rate_limit_key


def get_rate_limit_for_endpoint(path: str) -> str:
    """
    Get appropriate rate limit for an endpoint based on its path.
    
    Args:
        path: Request path
        
    Returns:
        Rate limit string (e.g., "60/minute")
    """
    if not RATE_LIMIT_ENABLED:
        return None
    
    # Health and root endpoints: more lenient
    if path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return f"{RATE_LIMIT_HEALTH_PER_MINUTE}/minute"
    
    # Plot/computation endpoints: stricter limits
    if "/plot/" in path:
        return f"{RATE_LIMIT_PLOT_PER_MINUTE}/minute"
    
    # Default rate limit for other endpoints
    return f"{RATE_LIMIT_PER_MINUTE}/minute"


# Rate limit decorators for different endpoint types
def rate_limit_data():
    """Rate limit decorator for data endpoints (default limit)."""
    if not RATE_LIMIT_ENABLED:
        return lambda f: f  # No-op decorator if rate limiting is disabled
    return limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")


def rate_limit_plot():
    """Rate limit decorator for plot/computation endpoints (stricter limit)."""
    if not RATE_LIMIT_ENABLED:
        return lambda f: f  # No-op decorator if rate limiting is disabled
    return limiter.limit(f"{RATE_LIMIT_PLOT_PER_MINUTE}/minute")


def rate_limit_health():
    """Rate limit decorator for health/root endpoints (more lenient limit)."""
    if not RATE_LIMIT_ENABLED:
        return lambda f: f  # No-op decorator if rate limiting is disabled
    return limiter.limit(f"{RATE_LIMIT_HEALTH_PER_MINUTE}/minute")


def apply_rate_limit(limit_str: str):
    """Apply rate limiting decorator if enabled."""
    if not RATE_LIMIT_ENABLED:
        return lambda f: f  # No-op decorator if rate limiting is disabled
    return limiter.limit(limit_str)
