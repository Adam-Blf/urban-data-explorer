"""Data quality checks for Gold datasets.

Computes per-dataset:
- completeness_pct  : fraction of non-null cells (0-100)
- out_of_range      : count of numeric values outside expected [min, max]
- row_count         : total rows
- freshness_days    : age of the Parquet file in days (mtime delta)

No external dependencies beyond polars and the standard library.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = ROOT / "data" / "gold"

# Expected numeric ranges for key columns (column -> (min, max)).
# Values outside these ranges are flagged as out-of-range.
RANGE_RULES: dict[str, tuple[float, float]] = {
    "prix_m2": (1_000.0, 50_000.0),
    "revenu_median": (5_000.0, 200_000.0),
    "logement_social_pct": (0.0, 100.0),
    "score": (0.0, 100.0),
    "immobilier_idx": (0.0, 100.0),
    "logement_social_idx": (0.0, 100.0),
    "revenu_idx": (0.0, 100.0),
    "cadre_vie_idx": (0.0, 100.0),
    "environnement_idx": (0.0, 100.0),
}


def _completeness(df: pl.DataFrame) -> float:
    """Return fraction of non-null cells as a percentage 0-100."""
    total = df.shape[0] * df.shape[1]
    if total == 0:
        return 100.0
    null_count = sum(df[col].null_count() for col in df.columns)
    return round((1.0 - null_count / total) * 100.0, 2)


def _out_of_range(df: pl.DataFrame) -> int:
    """Count cells that violate RANGE_RULES."""
    violations = 0
    for col, (lo, hi) in RANGE_RULES.items():
        if col not in df.columns:
            continue
        series = df[col].drop_nulls()
        violations += int((series < lo).sum() + (series > hi).sum())
    return violations


def _freshness_days(path: Path) -> float | None:
    """Return file age in days, or None if file doesn't exist."""
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    age_s = time.time() - mtime
    return round(age_s / 86400.0, 1)


def compute_quality() -> list[dict[str, Any]]:
    """Compute quality metrics for every Parquet in the Gold layer.

    Returns a list of dicts, one per dataset, suitable for JSON serialisation.
    """
    report: list[dict[str, Any]] = []

    for parquet_path in sorted(GOLD_DIR.glob("*.parquet")):
        try:
            df = pl.read_parquet(parquet_path)
        except Exception as exc:
            report.append({
                "dataset": parquet_path.name,
                "error": str(exc),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            })
            continue

        report.append({
            "dataset": parquet_path.name,
            "row_count": df.shape[0],
            "column_count": df.shape[1],
            "completeness_pct": _completeness(df),
            "out_of_range_count": _out_of_range(df),
            "freshness_days": _freshness_days(parquet_path),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })

    return report
