"""Build Gold – Construction des datamarts agrégés avec Polars.

Lit les données Silver, construit les datamarts dashboard et timeline,
puis écrit les résultats en Parquet et (optionnellement) dans PostgreSQL.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from io import BytesIO
from pathlib import Path

import polars as pl

from etl.metrics import record_stage
from etl.processing import build_gold_dashboard, build_gold_timeline

ROOT = Path(__file__).resolve().parents[2]
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"

logger = logging.getLogger(__name__)


def _write_pg(table: str, frame: pl.DataFrame) -> None:
    """Charge un DataFrame dans PostgreSQL via COPY avec liste de colonnes explicite."""
    try:
        import psycopg2
        conn = psycopg2.connect(host="postgres", port=5432, dbname="ude", user="ude", password="ude")
        # BytesIO requis : polars.write_csv écrit en binaire sur les file-like objects
        buffer = BytesIO()
        frame.write_csv(buffer)
        buffer.seek(0)
        # Liste de colonnes explicite : sécurise l'ordre COPY vs ordre de la table
        cols = ", ".join(frame.columns)
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table}")
            cur.copy_expert(f"COPY {table} ({cols}) FROM STDIN WITH CSV HEADER", buffer)
        conn.commit()
        conn.close()
        print(f"  -> PostgreSQL: {table} ({len(frame)} lignes)")
    except Exception as exc:
        logger.warning("PostgreSQL indisponible (normal hors-ligne) pour %s : %s", table, exc)


def main():
    print("=" * 60)
    print("  Urban Data Explorer - Build Gold (Polars)")
    print("=" * 60)

    silver_path = SILVER_DIR / "all_sources.parquet"
    if not silver_path.exists():
        print("  [ERROR] Pas de donnees Silver. Executez d'abord batch_ingest.py")
        return

    silver_df = pl.read_parquet(silver_path)
    rows_silver = len(silver_df)
    print(f"  Silver: {rows_silver} enregistrements")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # ── Dashboard ────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    dashboard = build_gold_dashboard(silver_df)
    t_dash = time.perf_counter() - t0

    if not dashboard.is_empty():
        dash_path = GOLD_DIR / "dashboard.parquet"
        dashboard.write_parquet(dash_path)
        bytes_dash = dash_path.stat().st_size
        print(f"  Gold dashboard: {len(dashboard)} lignes")
        record_stage("gold_dashboard", rows_silver, len(dashboard), t_dash, bytes_dash)
        _write_pg("fact_arrondissement_dashboard", dashboard)

    # ── Timeline ─────────────────────────────────────────────────────────
    t1 = time.perf_counter()
    timeline = build_gold_timeline(silver_df)
    t_tl = time.perf_counter() - t1

    if not timeline.is_empty():
        tl_path = GOLD_DIR / "timeline.parquet"
        timeline.write_parquet(tl_path)
        bytes_tl = tl_path.stat().st_size
        print(f"  Gold timeline: {len(timeline)} lignes")
        record_stage("gold_timeline", rows_silver, len(timeline), t_tl, bytes_tl)
        _write_pg("fact_arrondissement_timeline", timeline)

    # ── Pipeline run log ─────────────────────────────────────────────────
    today = str(date.today())
    try:
        import psycopg2
        conn = psycopg2.connect(host="postgres", port=5432, dbname="ude", user="ude", password="ude")
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pipeline_runs (run_date, stage, status, row_count) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (run_date, stage) DO UPDATE SET status = EXCLUDED.status, row_count = EXCLUDED.row_count",
                (today, "gold", "done", int(dashboard.height + timeline.height)),
            )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("Impossible d'enregistrer le run pipeline dans PostgreSQL : %s", exc)

    print("\n  Build Gold termine.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
