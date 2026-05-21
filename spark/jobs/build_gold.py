"""Build Gold – Construction des datamarts agrégés avec Polars.

Lit les données Silver, construit les datamarts dashboard et timeline,
puis écrit les résultats en Parquet et (optionnellement) dans PostgreSQL.
"""

from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path

import polars as pl

from etl.processing import build_gold_dashboard, build_gold_timeline

ROOT = Path(__file__).resolve().parents[2]
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"


def _write_pg(table: str, frame: pl.DataFrame) -> None:
    """Charge un DataFrame dans PostgreSQL via COPY."""
    try:
        import psycopg2
        conn = psycopg2.connect(host="postgres", port=5432, dbname="ude", user="ude", password="ude")
        buffer = StringIO()
        frame.write_csv(buffer)
        buffer.seek(0)
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table}")
            cur.copy_expert(f"COPY {table} FROM STDIN WITH CSV HEADER", buffer)
        conn.commit()
        conn.close()
        print(f"  -> PostgreSQL: {table} ({len(frame)} lignes)")
    except Exception as exc:
        print(f"  [INFO] PostgreSQL indisponible (normal hors-ligne): {exc}")


def main():
    print("=" * 60)
    print("  Urban Data Explorer - Build Gold (Polars)")
    print("=" * 60)

    silver_path = SILVER_DIR / "all_sources.parquet"
    if not silver_path.exists():
        print("  [ERROR] Pas de donnees Silver. Executez d'abord batch_ingest.py")
        return

    silver_df = pl.read_parquet(silver_path)
    print(f"  Silver: {len(silver_df)} enregistrements")

    dashboard = build_gold_dashboard(silver_df)
    timeline = build_gold_timeline(silver_df)

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    if not dashboard.is_empty():
        dashboard.write_parquet(GOLD_DIR / "dashboard.parquet")
        print(f"  Gold dashboard: {len(dashboard)} lignes")
        _write_pg("fact_arrondissement_dashboard", dashboard)

    if not timeline.is_empty():
        timeline.write_parquet(GOLD_DIR / "timeline.parquet")
        print(f"  Gold timeline: {len(timeline)} lignes")
        _write_pg("fact_arrondissement_timeline", timeline)

    # Log le run
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
    except Exception:
        pass

    print("\n  Build Gold termine.")


if __name__ == "__main__":
    main()
