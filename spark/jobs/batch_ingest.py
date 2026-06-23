"""Batch ingest – Chargement des CSV bruts vers Parquet (Bronze) avec Polars.

C2.3 : Transformation des données provenant de différentes sources.
C2.4 : Optimisation des pipelines de données.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.catalog import ALL_SOURCES
from etl.io import load_source_as_silver
from etl.scraper import download_dataset

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw" / "downloads"
BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"


def main():
    """Point d'entrée du batch ingest."""
    print("=" * 60)
    print("  Urban Data Explorer - Batch Ingest (Polars)")
    print("=" * 60)

    print("\n  [Step 1/2] Synchronisation des données depuis Open Data Paris...")
    success_count = sum(
        1 for spec in ALL_SOURCES if not spec.metadata_only and download_dataset(spec, DATA_DIR)
    )
    print(f"  Synchronisation terminée : {success_count} fichiers téléchargés.")

    print("\n  [Step 2/2] Traitement des données...")
    all_silver: list[pl.DataFrame] = []
    for spec in ALL_SOURCES:
        silver = load_source_as_silver(spec, DATA_DIR)
        if not silver.is_empty():
            print(f"  [OK] {spec.source_id}: {len(silver)} enregistrements")
            all_silver.append(silver)

    if all_silver:
        combined = pl.concat(all_silver, how="vertical_relaxed")

        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        combined.write_parquet(BRONZE_DIR / "all_sources.parquet")
        print(f"\n  Bronze: {len(combined)} lignes -> {BRONZE_DIR / 'all_sources.parquet'}")

        SILVER_DIR.mkdir(parents=True, exist_ok=True)
        combined.write_parquet(SILVER_DIR / "all_sources.parquet")
        print(f"  Silver: {len(combined)} lignes -> {SILVER_DIR / 'all_sources.parquet'}")

    print("\n  Pipeline termine.")


if __name__ == "__main__":
    main()
