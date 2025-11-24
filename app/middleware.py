"""
Security middleware for OpenChemFacts Backend API.

This module provides middleware for:
- Security HTTP headers
- Request size limiting
- Security logging
"""
import os
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

logger = logging.getLogger(__name__)

# Configuration from environment variables
ENABLE_SECURITY_HEADERS = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "1048576"))  # Default: 1MB


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security HTTP headers to all responses.
    
    Adds headers to protect against common web vulnerabilities:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables XSS filtering
    - Strict-Transport-Security: Forces HTTPS (if enabled)
    - Content-Security-Policy: Basic CSP policy
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        if ENABLE_SECURITY_HEADERS:
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # Enable XSS protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Basic Content Security Policy
            # Allow same-origin and data URIs for images, scripts, styles
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
            
            # HSTS - Only add if HTTPS is detected
            # In production behind a proxy, the proxy should handle this
            # But we can add it if X-Forwarded-Proto indicates HTTPS
            if request.headers.get("X-Forwarded-Proto") == "https":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server information (security best practice)
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit the size of request bodies.
    
    Prevents large payload attacks by rejecting requests that exceed
    the configured maximum size.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    logger.warning(
                        f"Request rejected: body size {size} exceeds limit {MAX_REQUEST_SIZE}. "
                        f"IP: {request.client.host if request.client else 'unknown'}, "
                        f"Path: {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request body too large. Maximum size: {MAX_REQUEST_SIZE} bytes"
                        }
                    )
            except ValueError:
                # Invalid content-length header, let it pass (will be handled by FastAPI)
                pass
        
        # For streaming requests, we rely on FastAPI's built-in size limits
        response = await call_next(request)
        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log security-relevant events.
    
    Logs:
    - Request IP addresses
    - Request paths
    - User agents
    - Response status codes
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP (considering proxies)
        client_ip = request.client.host if request.client else "unknown"
        if "X-Forwarded-For" in request.headers:
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        
        # Log request
        user_agent = request.headers.get("user-agent", "unknown")
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} "
            f"(User-Agent: {user_agent})"
        )
        
        response = await call_next(request)
        
        # Log security-relevant responses
        if response.status_code >= 400:
            logger.warning(
                f"Error response: {response.status_code} for {request.method} {request.url.path} "
                f"from {client_ip}"
            )
        
        return response

