import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import api

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="openchemfacts_API_0.1",
    version="0.1.0",
)

# Log au démarrage pour le débogage
logger.info("Starting OpenChemFacts API")
logger.info(f"Python version: {sys.version}")

# Configuration CORS pour permettre les appels depuis le frontend
# Par défaut, autorise https://openchemfacts.com, https://openchemfacts.lovable.app et les domaines Lovable
# Peut être configuré via la variable d'environnement ALLOWED_ORIGINS
# (séparer les origines par des virgules)
# Pour les sous-domaines Lovable, on utilise allow_origin_regex
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "https://openchemfacts.com,https://openchemfacts.lovable.app,https://lovableproject.com,http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

# Regex pour autoriser tous les sous-domaines de lovableproject.com et localhost en développement
lovable_regex = r"https://.*\.lovableproject\.com"
localhost_regex = r"http://localhost:\d+|http://127\.0\.0\.1:\d+"

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=f"{lovable_regex}|{localhost_regex}",  # Autorise tous les sous-domaines de lovableproject.com et localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/")
def root():
    """Route racine avec informations sur l'API."""
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
    """Health check endpoint pour vérifier l'état de l'API."""
    from datetime import datetime
    
    try:
        # Vérifier que les données peuvent être chargées
        from .data_loader import load_data
        df = load_data()
        data_status = "ok"
        data_rows = len(df)
    except Exception as e:
        data_status = f"error: {str(e)}"
        data_rows = 0
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "status": data_status,
            "rows": data_rows
        },
        "version": "0.1.0"
    }
