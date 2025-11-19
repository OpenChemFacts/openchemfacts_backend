"""
Main application file for OpenChemFacts Backend API.

This module creates and configures the FastAPI application, including:
- CORS configuration for frontend access
- API route registration
- Health check and root endpoints
"""
import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import api

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title="openchemfacts_API_0.1",
    version="0.1.0",
    description="API for accessing ecotoxicology data and generating scientific visualizations",
)

# Log au démarrage pour le débogage
logger.info("Starting OpenChemFacts API")
logger.info(f"Python version: {sys.version}")

# Configuration CORS (Cross-Origin Resource Sharing)
# Permet au frontend d'appeler l'API depuis différents domaines
# 
# Configuration par défaut :
# - Autorise les domaines de production (openchemfacts.com, lovableproject.com)
# - Autorise localhost pour le développement
# 
# Personnalisation :
# - Définir la variable d'environnement ALLOWED_ORIGINS (séparer par des virgules)
# - Exemple : export ALLOWED_ORIGINS=https://example.com,https://www.example.com
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "https://openchemfacts.com,https://openchemfacts.lovable.app,https://lovableproject.com,http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

# Regex pour autoriser automatiquement :
# - Tous les sous-domaines de lovableproject.com
# - Tous les ports de localhost (pour le développement)
lovable_regex = r"https://.*\.lovableproject\.com"
localhost_regex = r"http://localhost:\d+|http://127\.0\.0\.1:\d+"

logger.info(f"CORS allowed origins: {allowed_origins}")

# Ajouter le middleware CORS à l'application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=f"{lovable_regex}|{localhost_regex}",
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)

# Enregistrer les routes API définies dans api.py
# Toutes les routes seront préfixées par /api
app.include_router(api.router, prefix="/api", tags=["api"])


@app.get("/")
def root():
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
def health():
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
