"""
Main application file for OpenChemFacts Backend API.

This module creates and configures the FastAPI application, including:
- CORS configuration for frontend access
- Security middleware (rate limiting, security headers, request size limits)
- API route registration
- Health check and root endpoints
"""
import os
import sys
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from . import api
from .middleware import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    SecurityLoggingMiddleware
)
from .security import limiter, RATE_LIMIT_ENABLED, RATE_LIMIT_HEALTH_PER_MINUTE

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title="openchemfacts_API_0.1",
    version="0.1.0",
    description="API for accessing ecotoxicology data and generating scientific visualizations",
)

# Initialize rate limiter
app.state.limiter = limiter

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors.
    
    Returns a 429 Too Many Requests response with retry-after information.
    """
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.retry_after
        }
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response

# Log au démarrage pour le débogage
logger.info("Starting OpenChemFacts API")
logger.info(f"Python version: {sys.version}")

# Configuration CORS (Cross-Origin Resource Sharing)
# Permet au frontend d'appeler l'API depuis différents domaines
# 
# Configuration par défaut (utilisée si ALLOWED_ORIGINS n'est pas définie) :
# - Autorise les domaines de production (openchemfacts.com, www.openchemfacts.com)
# - Autorise les domaines Lovable (*.lovable.app et *.lovableproject.com via regex)
# - Autorise localhost pour le développement
# 
# ⚠️ IMPORTANT - Configuration en production (Scalingo) :
# La liste des origines autorisées doit être définie via la variable d'environnement
# ALLOWED_ORIGINS sur Scalingo, PAS dans le code source.
# 
# Pour configurer sur Scalingo :
#   scalingo env-set ALLOWED_ORIGINS=https://openchemfacts.com,https://www.openchemfacts.com
# 
# Pour le développement local :
#   export ALLOWED_ORIGINS=https://example.com,https://www.example.com
#   (ou définir dans votre IDE/environnement de développement)
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "https://openchemfacts.com,https://www.openchemfacts.com,https://openchemfacts.lovable.app,https://lovableproject.com,http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

# Regex pour autoriser automatiquement :
# - Tous les sous-domaines de lovable.app (domaines Lovable en production)
# - Tous les sous-domaines de lovableproject.com
# - Tous les ports de localhost (pour le développement)
lovable_app_regex = r"https://.*\.lovable\.app"
lovableproject_regex = r"https://.*\.lovableproject\.com"
localhost_regex = r"http://localhost:\d+|http://127\.0\.0\.1:\d+"

logger.info(f"CORS allowed origins: {allowed_origins}")

# Add security middleware (order matters - add before CORS)
# Security logging should be first to log all requests
app.add_middleware(SecurityLoggingMiddleware)

# Request size limiting
app.add_middleware(RequestSizeLimitMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Ajouter le middleware CORS à l'application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=f"{lovable_app_regex}|{lovableproject_regex}|{localhost_regex}",
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)

# Enregistrer les routes API définies dans api.py
# Toutes les routes seront préfixées par /api
app.include_router(api.router, prefix="/api", tags=["api"])


@app.get("/")
@limiter.limit(f"{RATE_LIMIT_HEALTH_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
def root(_request: Request):
    """
    Root endpoint providing API information and available endpoints.
    
    Returns:
        Dictionary containing:
        - message: API name and version
        - status: Current API status
        - endpoints: List of available API endpoints with descriptions
    """
    return {
        "message": "OpenChemFacts API v0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "documentation": "/docs",
            "redoc": "/redoc",
            "api_summary": "/api/summary",
            "api_cas_list": "/api/cas/list",
            "api_search": "/api/search?query={query}&limit={limit}",
            "api_plot_ssd": "/api/plot/ssd/{identifier}",
            "api_plot_ec10eq": "/api/plot/ec10eq/{identifier}",
            "api_plot_comparison": "/api/plot/ssd/comparison"
        }
    }


@app.get("/health")
@limiter.limit(f"{RATE_LIMIT_HEALTH_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
def health(_request: Request):
    """
    Health check endpoint to verify API and data availability.
    
    This endpoint is used by:
    - Monitoring systems to check API status
    - Scalingo health checks (if configured)
    - Development to verify the server is running correctly
    
    Returns:
        Dictionary containing:
        - status: Overall API status (always "ok" if endpoint is reachable)
        - timestamp: Current UTC timestamp
        - data: Data loading status and row count
        - version: API version number
    """
    from datetime import datetime
    
    try:
        # Vérifier que les données peuvent être chargées
        from .data_loader import load_data
        df = load_data()
        data_status = "ok"
        data_rows = len(df)
    except Exception as e:
        # Si le chargement échoue, on retourne quand même une réponse
        # mais avec un statut d'erreur dans data.status
        data_status = f"error: {str(e)}"
        data_rows = 0
        logger.error(f"Health check failed to load data: {str(e)}")
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "status": data_status,
            "rows": data_rows
        },
        "version": "0.1.0"
    }
