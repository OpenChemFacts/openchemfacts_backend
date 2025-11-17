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
# En production, restreint à https://openchemfacts.com
# Peut être configuré via la variable d'environnement ALLOWED_ORIGINS
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://openchemfacts.com"
).split(",")

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
