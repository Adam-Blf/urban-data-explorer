from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import auth, catalog, datamarts, events, health, pipeline, repo
from .security import check_quota

# Mode exe local-first : si UDE_STATIC_DIR pointe vers un build front (dist),
# l'API sert aussi la SPA -> un seul processus, meme origine, hors ligne.
_STATIC_DIR = os.getenv("UDE_STATIC_DIR")

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
    # En mode exe local-first, la racine sert la SPA ; sinon, infos JSON de l'API.
    if _STATIC_DIR:
        return FileResponse(Path(_STATIC_DIR) / "index.html")
    return {
        "name": "Urban Data Explorer",
        "status": "ok",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# Service du front builde (exe local-first uniquement). Les routes API ci-dessus
# sont enregistrees avant, donc elles priment ; le catch-all gere le routage SPA.
if _STATIC_DIR and Path(_STATIC_DIR).is_dir():
    _sd = Path(_STATIC_DIR)
    for _sub in ("assets", "fonts"):
        if (_sd / _sub).is_dir():
            app.mount(f"/{_sub}", StaticFiles(directory=_sd / _sub), name=_sub)

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa(full_path: str):
        candidate = _sd / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_sd / "index.html")
