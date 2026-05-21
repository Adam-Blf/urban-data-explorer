from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalog, datamarts, events, health, pipeline, repo

tags_metadata = [
    {"name": "health", "description": "État local du projet."},
    {"name": "catalog", "description": "Catalogue de sources intégrées."},
    {"name": "datamarts", "description": "Données de synthèse et carte."},
    {"name": "pipeline", "description": "Dernier run du pipeline."},
    {"name": "events", "description": "Derniers événements simulés."},
    {"name": "repo", "description": "Badges de préparation du repo."},
]

app = FastAPI(
    title="Urban Data Explorer",
    description="API backend pour le dashboard Paris – logement, mobilité, éducation, culture, espaces verts.",
    version="4.0.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
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
