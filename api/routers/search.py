"""Semantic search router – GET /search/semantic?q=<query>&top_k=<n>

Uses TF-IDF hashing vectors (64 dims) with pgvector when available,
falls back to in-memory cosine similarity otherwise.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/semantic", response_model=list[dict[str, Any]])
def semantic_search(
    q: str = Query(..., min_length=1, description="Texte de recherche libre (ex : 'quartier vert calme')"),
    top_k: int = Query(5, ge=1, le=20, description="Nombre de résultats"),
):
    """Recherche sémantique sur les arrondissements de Paris.

    Retourne les arrondissements les plus proches du texte de requête
    par similarité cosinus sur vecteurs TF-IDF (64 dimensions).
    - backend pgvector : si PostgreSQL + extension vector est disponible.
    - backend memory  : sinon, calcul en mémoire (déterministe, hors-ligne).
    """
    from ..search import semantic_search as _search
    return _search(q, top_k=top_k)
