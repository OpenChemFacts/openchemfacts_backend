from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import api

app = FastAPI(
    title="openchemfacts_API_0.1",
    version="0.1.0",
)

# Configuration CORS pour permettre les appels depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacer par les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/health")
def health():
    return {"status": "ok"}
