"""Router /pipeline – suivi du pipeline ETL et qualite des donnees (C1.3 / C2.4).

Routes :
- GET /pipeline/latest  : dernier run ETL (date, stage, status, row_count).
  Source prioritaire : table pipeline_runs PostgreSQL ; fallback : generateur.
- GET /pipeline/metrics : derniers N runs avec duree, debit (rows/sec), bytes ecrits.
  Donnees issues de data/metrics/pipeline_metrics.parquet (ecrit par etl/metrics.py).
- GET /pipeline/quality : rapport de qualite des datasets Gold (completeness, out-of-range,
  freshness). Calcule en temps reel sur data/gold/*.parquet.
"""

from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Query
from ..schemas import PipelineRun

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/latest", response_model=PipelineRun | None)
def latest_run():
    """Return the most recent pipeline execution status."""
    try:
        from ..db import pg_fetch_all
        rows = pg_fetch_all(
            """
            SELECT run_date, stage, status, row_count, updated_at
            FROM pipeline_runs
            ORDER BY updated_at DESC
            LIMIT 1
            """
        )
        return PipelineRun(**rows[0]) if rows else None
    except Exception:
        from ..data import latest_pipeline_run
        return PipelineRun(**latest_pipeline_run())


@router.get("/metrics", response_model=list[dict[str, Any]])
def pipeline_metrics(limit: int = Query(50, ge=1, le=500)):
    """Retourne les dernières métriques de pipeline (durée, débit, comptages).

    Données issues de data/metrics/pipeline_metrics.parquet (C2.4/C1.3).
    """
    from etl.metrics import load_metrics
    return load_metrics(limit=limit)


@router.get("/quality", response_model=list[dict[str, Any]])
def pipeline_quality():
    """Rapport de qualité des datasets Gold.

    Pour chaque fichier Parquet de la couche Gold :
    - completeness_pct : fraction de cellules non-nulles (0-100)
    - out_of_range_count : cellules hors des plages attendues
    - row_count, column_count : dimensions
    - freshness_days : ancienneté du fichier en jours
    """
    from etl.quality import compute_quality
    return compute_quality()
