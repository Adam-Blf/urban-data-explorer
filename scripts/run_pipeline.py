"""Pipeline complet Bronze/Silver/Gold sans retelecharger les sources.

Execute apres auto_ingest.py une fois les CSV/TSV telecharges.
Usage: python scripts/run_pipeline.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import polars as pl

from etl.catalog import ALL_SOURCES
from etl.io import load_source_as_silver
from etl.processing import build_gold_dashboard, build_gold_timeline

DATA_DIR = ROOT / "data" / "raw" / "downloads"
BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"


def main() -> None:
    print("=" * 60)
    print("  Urban Data Explorer - Pipeline Bronze/Silver/Gold")
    print("=" * 60)

    t0 = time.perf_counter()
    all_silver: list[pl.DataFrame] = []
    for spec in ALL_SOURCES:
        df = load_source_as_silver(spec, DATA_DIR)
        if not df.is_empty():
            print(f"  [OK] {spec.source_id}: {len(df)} lignes")
            all_silver.append(df)

    if not all_silver:
        print("[ERROR] Aucune donnee trouvee dans data/raw/downloads/")
        print("  -> Lancez d'abord: python scripts/auto_ingest.py")
        sys.exit(1)

    combined = pl.concat(all_silver, how="vertical_relaxed")
    print(f"\nBronze/Silver: {len(combined)} lignes ({time.perf_counter() - t0:.1f}s)")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    combined.write_parquet(BRONZE_DIR / "all_sources.parquet")
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    combined.write_parquet(SILVER_DIR / "all_sources.parquet")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    dashboard = build_gold_dashboard(combined)
    if not dashboard.is_empty():
        dashboard.write_parquet(GOLD_DIR / "dashboard.parquet")
        print(f"Gold dashboard: {len(dashboard)} lignes")

    timeline = build_gold_timeline(combined)
    if not timeline.is_empty():
        timeline.write_parquet(GOLD_DIR / "timeline.parquet")
        print(f"Gold timeline: {len(timeline)} lignes")

    print(f"\nPipeline termine en {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
