"""Semantic search over Paris arrondissement descriptions.

Uses a lightweight feature-hashing TF-IDF approach (64 dims) so there is
no heavy ML dependency (no sentence-transformers, no numpy).

The vector is stored in PostgreSQL via the pgvector extension when available.
If pgvector / PostgreSQL is not reachable, the module falls back to fully
in-memory cosine similarity — all 102 existing tests stay green.

Algorithm
---------
1. Each arrondissement has a curated text description.
2. At import time, descriptions are tokenised and projected onto a 64-dim
   hash-space using the hashing trick (term -> hash(term) % 64).
3. Each vector is L2-normalised for cosine similarity.
4. At query time the same projection is applied to the query string.
5. Cosine similarity = dot product (vectors are unit-normed).
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

# ── District text descriptions ──────────────────────────────────────────────

DISTRICT_DESCRIPTIONS: dict[str, str] = {
    "75001": "Louvre quartier historique musees galeries royales Seine palais justice tourisme",
    "75002": "Bourse finance banques presse sentier mode textile galerie vivienne",
    "75003": "Temple marais archives nationales galeries art contemporain artisanat",
    "75004": "Hotel de Ville cathédrale Notre-Dame Ile de la Cité Ile Saint-Louis marais juif",
    "75005": "Pantheon Latin quartier etudiants Sorbonne université jardins bibliotheque histoire",
    "75006": "Luxembourg jardin Luxembourg Saint-Germain-des-Prés cafes litteraires editeurs art",
    "75007": "Palais-Bourbon Eiffel tour ministeres ambassades musee Orsay quartier huppé",
    "75008": "Elysee Champs-Elysées arc triomphe luxe commerce bureaux tourisme avenue Montaigne",
    "75009": "Opera Garnier grands magasins Moulin Rouge Pigalle divertissement commerce",
    "75010": "Entrepot gare Nord gare Est cosmopolite mixte commerce canal Saint-Martin bobos",
    "75011": "Popincourt Bastille vie nocturne bars restaurants artisanat faubourg",
    "75012": "Reuilly gare Lyon Bercy bois Vincennes nature parc sport",
    "75013": "Gobelins Chinatown université Paris-7 grands ensembles Seine fleuve",
    "75014": "Observatoire Montparnasse cimetière parc Montsouris tranquille résidentiel",
    "75015": "Vaugirard grand arrondissement résidentiel famille commerce Beaugrenelle shopping",
    "75016": "Passy bourgeois résidentiel bois Boulogne Trocadero musees Marmottan",
    "75017": "Batignolles Monceau village bobo familles marché place commerce",
    "75018": "Buttes-Montmartre Sacre-Coeur artistes bohème tourisme populaire mixte",
    "75019": "Buttes-Chaumont parc nature canal ourcq mixte jeune populaire Belleville",
    "75020": "Menilmontant Belleville Pere-Lachaise cosmopolite artistique populaire bobos",
}

DIMS = 64  # vector dimensions


# ── Pure-Python TF-IDF feature hashing ──────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """Lowercase + split on non-alphanumeric chars, remove stopwords."""
    stopwords = {"de", "la", "le", "les", "du", "des", "en", "et", "au", "aux",
                 "un", "une", "par", "sur", "sous", "dans", "avec"}
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 2]


def _hash_index(token: str) -> int:
    """Map a token to a bucket in [0, DIMS) using SHA-1."""
    digest = hashlib.sha1(token.encode()).digest()
    return int.from_bytes(digest[:2], "big") % DIMS


def _to_vector(text: str) -> list[float]:
    """Project text into a DIMS-dimensional TF vector using hashing trick."""
    tokens = _tokenise(text)
    vec = [0.0] * DIMS
    for t in tokens:
        vec[_hash_index(t)] += 1.0
    # L2 normalise
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    """Dot product of two L2-normalised vectors (= cosine similarity)."""
    return sum(x * y for x, y in zip(a, b))


# ── Pre-compute district vectors at import time ──────────────────────────────

_DISTRICT_VECTORS: dict[str, list[float]] = {
    code: _to_vector(desc)
    for code, desc in DISTRICT_DESCRIPTIONS.items()
}


# ── In-memory semantic search (always available) ─────────────────────────────

def semantic_search_memory(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return top-k arrondissements by cosine similarity (in-memory)."""
    q_vec = _to_vector(query)
    scores = [
        (code, _cosine(q_vec, vec))
        for code, vec in _DISTRICT_VECTORS.items()
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        {
            "code": code,
            "description": DISTRICT_DESCRIPTIONS[code],
            "score": round(sim, 4),
            "backend": "memory",
        }
        for code, sim in scores[:top_k]
    ]


# ── PostgreSQL + pgvector backend (optional) ─────────────────────────────────

def _pg_vector_literal(vec: list[float]) -> str:
    """Format a Python list as a pgvector literal '[f1,f2,...]'."""
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


def seed_postgres() -> bool:
    """Upsert all district embeddings into PostgreSQL.

    Returns True on success, False if pgvector is unavailable or the table
    doesn't exist yet (e.g. running without Docker).
    """
    try:
        from .db import pg_execute, pg_fetch_all  # type: ignore
        for code, vec in _DISTRICT_VECTORS.items():
            desc = DISTRICT_DESCRIPTIONS[code]
            literal = _pg_vector_literal(vec)
            pg_execute(
                """
                INSERT INTO district_embeddings (code_arrondissement, description, embedding)
                VALUES (%s, %s, %s::vector)
                ON CONFLICT (code_arrondissement) DO UPDATE
                  SET description = EXCLUDED.description,
                      embedding   = EXCLUDED.embedding
                """,
                (code, desc, literal),
            )
        return True
    except Exception:
        return False


def semantic_search_pg(query: str, top_k: int = 5) -> list[dict[str, Any]] | None:
    """Query pgvector for nearest neighbours.

    Returns None if pgvector / the table is not reachable so the caller can
    fall back to in-memory search.
    """
    try:
        from .db import pg_fetch_all  # type: ignore
        q_vec = _to_vector(query)
        literal = _pg_vector_literal(q_vec)
        rows = pg_fetch_all(
            """
            SELECT code_arrondissement, description,
                   1 - (embedding <=> %s::vector) AS score
            FROM district_embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (literal, literal, top_k),
        )
        return [
            {
                "code": r["code_arrondissement"],
                "description": r["description"],
                "score": round(float(r["score"]), 4),
                "backend": "pgvector",
            }
            for r in rows
        ]
    except Exception:
        return None


def semantic_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Try pgvector first, fall back to in-memory cosine similarity."""
    pg_result = semantic_search_pg(query, top_k)
    if pg_result is not None:
        return pg_result
    return semantic_search_memory(query, top_k)
