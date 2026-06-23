"""Batch ingest – Chargement des CSV bruts vers Parquet (Bronze) avec Polars.

C2.3 : Transformation des données provenant de différentes sources.
C2.4 : Optimisation des pipelines de données.
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl

from etl.catalog import ALL_SOURCES
from etl.processing import build_silver_record
from etl.scraper import download_dataset

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw" / "downloads"
BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"


def ingest_source(spec) -> pl.DataFrame:
    """Charge un fichier brut (CSV/TSV/GZ) et retourne un DataFrame Silver."""
    # Cherche dans l'ordre: .csv, .tsv, .csv.gz
    for ext in (".csv", ".tsv", ".csv.gz"):
        candidate = DATA_DIR / f"{spec.source_id}{ext}"
        if candidate.exists():
            csv_path = candidate
            break
    else:
        return pl.DataFrame()

    start = time.perf_counter()
    sep = "\t" if csv_path.suffix == ".tsv" else spec.separator

    try:
        df = pl.read_csv(
            csv_path,
            separator=sep,
            encoding=spec.encoding if spec.encoding != "utf-8-sig" else "utf8",
            infer_schema_length=500,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )
    except Exception as exc:
        print(f"  [ERROR] Erreur lecture {spec.source_id}: {exc}")
        return pl.DataFrame()

    # Transformation Bronze → Silver
    records = []
    for row in df.iter_rows(named=True):
        silver = build_silver_record(row, spec)
        records.append(silver)

    elapsed = time.perf_counter() - start
    print(f"  [OK] {spec.source_id}: {len(records)} enregistrements ({elapsed:.2f}s)")

    return pl.DataFrame(records) if records else pl.DataFrame()


def main():
    """Point d'entrée du batch ingest."""
    print("=" * 60)
    print("  Urban Data Explorer - Batch Ingest (Polars)")
    print("=" * 60)

    # --- Étape de téléchargement automatique ---
    print("\n  [Step 1/2] Synchronisation des données depuis Open Data Paris...")
    success_count = 0
    for spec in ALL_SOURCES:
        if download_dataset(spec, DATA_DIR):
            success_count += 1
    print(f"  Synchronisation terminée : {success_count}/{len(ALL_SOURCES)} fichiers téléchargés.")

    all_silver: list[pl.DataFrame] = []

    print("\n  [Step 2/2] Traitement des données...")
    for spec in ALL_SOURCES:
        silver = ingest_source(spec)
        if not silver.is_empty():
            all_silver.append(silver)

    if all_silver:
        combined = pl.concat(all_silver, how="vertical_relaxed")

        # Sauvegarde Bronze (Parquet)
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        combined.write_parquet(BRONZE_DIR / "all_sources.parquet")
        print(f"\n  Bronze: {len(combined)} lignes -> {BRONZE_DIR / 'all_sources.parquet'}")

        # Sauvegarde Silver (Parquet)
        SILVER_DIR.mkdir(parents=True, exist_ok=True)
        combined.write_parquet(SILVER_DIR / "all_sources.parquet")
        print(f"  Silver: {len(combined)} lignes -> {SILVER_DIR / 'all_sources.parquet'}")

    print("\n  Pipeline termine.")


if __name__ == "__main__":
    main()
