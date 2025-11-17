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
# Par défaut, autorise https://openchemfacts.com et https://openchemfacts.lovable.app
# Peut être configuré via la variable d'environnement ALLOWED_ORIGINS
# (séparer les origines par des virgules)
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "https://openchemfacts.com,https://openchemfacts.lovable.app"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/health")
def health():
    return {"status": "ok"}
