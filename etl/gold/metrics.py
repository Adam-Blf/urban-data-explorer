"""Métriques de pipeline ETL – C2.4 / C1.3.

Mesure et enregistre les durées, comptages et débits de chaque étape ETL.
Persiste les mesures dans data/metrics/pipeline_metrics.parquet (append).
Dépendance unique : polars.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "data" / "metrics"
METRICS_PATH = METRICS_DIR / "pipeline_metrics.parquet"


def record_stage(
    stage: str,
    rows_in: int,
    rows_out: int,
    duration_s: float,
    bytes_written: int = 0,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Enregistre les métriques d'une étape ETL et les persiste en Parquet (append).

    Args:
        stage: Nom de l'étape (ex : 'gold_dashboard', 'silver').
        rows_in: Nombre de lignes en entrée.
        rows_out: Nombre de lignes en sortie.
        duration_s: Durée de l'étape en secondes.
        bytes_written: Taille du fichier écrit en octets (0 si non applicable).
        run_id: Identifiant du run (généré automatiquement si absent).

    Returns:
        Dictionnaire des métriques enregistrées.
    """
    run_id = run_id or str(uuid.uuid4())[:8]
    rows_per_sec = rows_out / duration_s if duration_s > 0 else 0.0

    record: dict[str, Any] = {
        "run_id": run_id,
        "stage": stage,
        "started_at": datetime.now(timezone.utc),
        "duration_s": round(duration_s, 4),
        "rows_in": rows_in,
        "rows_out": rows_out,
        "rows_per_sec": round(rows_per_sec, 2),
        "bytes_written": bytes_written,
    }

    try:
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        new_df = pl.DataFrame(
            [record],
            schema={
                "run_id": pl.Utf8,
                "stage": pl.Utf8,
                "started_at": pl.Datetime("us", "UTC"),
                "duration_s": pl.Float64,
                "rows_in": pl.Int64,
                "rows_out": pl.Int64,
                "rows_per_sec": pl.Float64,
                "bytes_written": pl.Int64,
            },
        )

        if METRICS_PATH.exists():
            existing = pl.read_parquet(METRICS_PATH)
            combined = pl.concat([existing, new_df], how="diagonal")
        else:
            combined = new_df

        combined.write_parquet(METRICS_PATH)
    except Exception as exc:
        # Les métriques ne doivent jamais faire échouer le pipeline
        print(f"  [WARN] Écriture métriques échouée: {exc}")

    return record


def load_metrics(limit: int = 100) -> list[dict[str, Any]]:
    """Charge les dernières métriques depuis le Parquet.

    Args:
        limit: Nombre maximum de lignes à retourner (les plus récentes en premier).

    Returns:
        Liste de dictionnaires de métriques, triée par date décroissante.
    """
    if not METRICS_PATH.exists():
        return []
    try:
        df = (
            pl.read_parquet(METRICS_PATH)
            .sort("started_at", descending=True)
            .head(limit)
        )
        return df.to_dicts()
    except Exception:
        return []
