from __future__ import annotations

import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, catalog, datamarts, events, health, pipeline, repo
from .security import check_quota

tags_metadata = [
    {"name": "health", "description": "État local du projet."},
    {"name": "auth", "description": "Authentification JWT (OAuth2) et autorisations."},
    {"name": "catalog", "description": "Catalogue de sources intégrées."},
    {"name": "datamarts", "description": "Données de synthèse et carte."},
    {"name": "pipeline", "description": "Dernier run du pipeline."},
    {"name": "events", "description": "Derniers événements simulés."},
    {"name": "repo", "description": "Badges de préparation du repo."},
]

app = FastAPI(
    title="Urban Data Explorer",
    description="API backend pour le dashboard Paris · logement, mobilité, prix immobilier (DVF), revenus (INSEE Filosofi). Authentification JWT + quotas par IP.",
    version="4.1.0",
    openapi_tags=tags_metadata,
    # Quota par IP applique a toutes les routes (C2.1 · autorisations/quotas)
    dependencies=[Depends(check_quota)],
)

# CORS restreint a l'origine du frontend (override par UDE_CORS_ORIGINS)
_origins = os.getenv("UDE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(datamarts.router)
app.include_router(pipeline.router)
app.include_router(events.router)
app.include_router(repo.router)


@app.get("/", tags=["health"])
def root():
    return {
        "name": "Urban Data Explorer",
        "status": "ok",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
