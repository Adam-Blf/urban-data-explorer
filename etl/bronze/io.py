"""Chargement CSV/TSV/GZ → Silver DataFrame (Polars).

Point d'entrée unique utilisé par run_pipeline.py et spark/jobs/batch_ingest.py.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from .catalog import SourceSpec
from ..silver.processing import build_silver_record


def load_source_as_silver(spec: SourceSpec, data_dir: Path) -> pl.DataFrame:
    """Charge un fichier brut et retourne un DataFrame Silver normalisé."""
    if spec.metadata_only or spec.is_overpass and not _overpass_file_exists(spec, data_dir):
        return pl.DataFrame()

    for ext in (".csv", ".tsv", ".csv.gz"):
        path = data_dir / f"{spec.source_id}{ext}"
        if path.exists():
            break
    else:
        return pl.DataFrame()

    sep = "\t" if path.suffix == ".tsv" else spec.separator
    try:
        df = pl.read_csv(
            path,
            separator=sep,
            encoding=spec.polars_encoding,
            infer_schema_length=500,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )
    except Exception as exc:
        print(f"  [ERR] {spec.source_id}: {exc}")
        return pl.DataFrame()

    records = [build_silver_record(row, spec) for row in df.iter_rows(named=True)]
    return pl.DataFrame(records) if records else pl.DataFrame()


def _overpass_file_exists(spec: SourceSpec, data_dir: Path) -> bool:
    return any((data_dir / f"{spec.source_id}{ext}").exists() for ext in (".tsv", ".csv"))
