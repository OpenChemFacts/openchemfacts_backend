import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import api

app = FastAPI(
    title="openchemfacts_API_0.1",
    version="0.1.0",
)

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
