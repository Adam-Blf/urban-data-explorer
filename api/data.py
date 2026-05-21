"""Données local-first – fallback quand PostgreSQL/Cassandra ne sont pas accessibles.

Fournit des données calculées déterministes à partir du catalogue de sources,
permettant au dashboard de fonctionner sans aucun conteneur Docker.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from etl.catalog import ALL_SOURCES, FAMILIES

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw" / "downloads"

DISTRICTS = (
    {"code": "75001", "name": "Louvre", "label": "1er"},
    {"code": "75002", "name": "Bourse", "label": "2e"},
    {"code": "75003", "name": "Temple", "label": "3e"},
    {"code": "75004", "name": "Hôtel-de-Ville", "label": "4e"},
    {"code": "75005", "name": "Panthéon", "label": "5e"},
    {"code": "75006", "name": "Luxembourg", "label": "6e"},
    {"code": "75007", "name": "Palais-Bourbon", "label": "7e"},
    {"code": "75008", "name": "Élysée", "label": "8e"},
    {"code": "75009", "name": "Opéra", "label": "9e"},
    {"code": "75010", "name": "Entrepôt", "label": "10e"},
    {"code": "75011", "name": "Popincourt", "label": "11e"},
    {"code": "75012", "name": "Reuilly", "label": "12e"},
    {"code": "75013", "name": "Gobelins", "label": "13e"},
    {"code": "75014", "name": "Observatoire", "label": "14e"},
    {"code": "75015", "name": "Vaugirard", "label": "15e"},
    {"code": "75016", "name": "Passy", "label": "16e"},
    {"code": "75017", "name": "Batignolles-Monceau", "label": "17e"},
    {"code": "75018", "name": "Buttes-Montmartre", "label": "18e"},
    {"code": "75019", "name": "Buttes-Chaumont", "label": "19e"},
    {"code": "75020", "name": "Ménilmontant", "label": "20e"},
)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _digest(seed: str) -> float:
    return hashlib.sha1(seed.encode()).digest()[0] / 255.0


@lru_cache(maxsize=1)
def source_catalog():
    return [
        {
            "source_id": s.source_id,
            "title": s.title,
            "provider": s.provider,
            "family": s.family,
            "catalog_url": s.catalog_url,
            "metadata_only": s.metadata_only,
        }
        for s in ALL_SOURCES
    ]


@lru_cache(maxsize=1)
def source_family_counts():
    counts = Counter(s.family for s in ALL_SOURCES)
    return {k: counts.get(k, 0) for k in FAMILIES}


@lru_cache(maxsize=1)
def district_rows():
    # 1. Try PostgreSQL
    try:
        from .db import pg_fetch_all
        sql = """
            SELECT 
                arrondissement_code,
                green_space_count,
                mobility_count,
                public_service_count,
                education_count,
                culture_count,
                health_count,
                housing_count,
                pressure_count,
                accessibility_index,
                pressure_index,
                attractiveness_index
            FROM fact_arrondissement_dashboard
        """
        db_rows = pg_fetch_all(sql)
        if db_rows:
            rows = []
            for row in db_rows:
                code = row["arrondissement_code"]
                district = next((d for d in DISTRICTS if d["code"] == code), None)
                if not district:
                    continue
                
                try:
                    i = [d["code"] for d in DISTRICTS].index(code)
                except ValueError:
                    i = 0
                
                x = 300 + i * 25
                y = 200 + int(math.sin(i) * 100)
                
                acc = row["accessibility_index"]
                press = row["pressure_index"]
                attr = row["attractiveness_index"]
                score = round((acc + attr - press * 0.25) / 2)
                
                family_counts = {
                    "green_space": int(row["green_space_count"]),
                    "mobility": int(row["mobility_count"]),
                    "public_service": int(row["public_service_count"]),
                    "education": int(row["education_count"]),
                    "culture": int(row["culture_count"]),
                    "health": int(row["health_count"]),
                    "housing": int(row["housing_count"]),
                    "pressure": int(row["pressure_count"]),
                }
                
                rows.append({
                    "code": code,
                    "name": district["name"],
                    "label": district["label"],
                    "x": x,
                    "y": y,
                    "family_counts": family_counts,
                    "accessibility_index": round(acc),
                    "pressure_index": round(press),
                    "attractiveness_index": round(attr),
                    "score": score,
                })
            
            if rows:
                rows.sort(key=lambda r: r["code"])
                return rows
    except Exception as exc:
        print(f"  [INFO] PostgreSQL district_rows failed: {exc}")

    # 2. Try Parquet
    try:
        import polars as pl
        parquet_path = ROOT / "data" / "gold" / "dashboard.parquet"
        if parquet_path.exists():
            df = pl.read_parquet(parquet_path)
            rows = []
            for row in df.to_dicts():
                code = row["arrondissement_code"]
                district = next((d for d in DISTRICTS if d["code"] == code), None)
                if not district:
                    continue
                
                try:
                    i = [d["code"] for d in DISTRICTS].index(code)
                except ValueError:
                    i = 0
                
                x = 300 + i * 25
                y = 200 + int(math.sin(i) * 100)
                
                acc = row["accessibility_index"]
                press = row["pressure_index"]
                attr = row["attractiveness_index"]
                score = round((acc + attr - press * 0.25) / 2)
                
                family_counts = {
                    "green_space": int(row["green_space_count"]),
                    "mobility": int(row["mobility_count"]),
                    "public_service": int(row["public_service_count"]),
                    "education": int(row["education_count"]),
                    "culture": int(row["culture_count"]),
                    "health": int(row["health_count"]),
                    "housing": int(row["housing_count"]),
                    "pressure": int(row["pressure_count"]),
                }
                
                rows.append({
                    "code": code,
                    "name": district["name"],
                    "label": district["label"],
                    "x": x,
                    "y": y,
                    "family_counts": family_counts,
                    "accessibility_index": round(acc),
                    "pressure_index": round(press),
                    "attractiveness_index": round(attr),
                    "score": score,
                })
            
            if rows:
                rows.sort(key=lambda r: r["code"])
                return rows
    except Exception as exc:
        print(f"  [INFO] Parquet dashboard failed: {exc}")

    # 3. Fallback to math generator
    rows = []
    fam_counts = source_family_counts()

    for i, district in enumerate(DISTRICTS):
        bias = _digest(district["code"])
        c = 0.5 + 0.3 * math.sin(i * 0.7)
        counts = {}

        for family in FAMILIES:
            fb = _digest(f"{district['code']}:{family}")
            density = fam_counts.get(family, 0)
            base = 2 + round(fb * 4) + density // 3
            if family == "green_space":
                base = 2 + round((1 - c) * 5) + round(fb * 2) + density // 4
            elif family == "mobility":
                base = 3 + round((0.6 + bias) * 4) + density // 3
            elif family == "education":
                base = 2 + round((0.35 + c) * 5) + density // 4
            counts[family] = max(0, base)

        accessibility = clamp(
            34 + counts["green_space"] * 2.5 + counts["mobility"] * 4
            + counts["public_service"] * 5.5 + counts["education"] * 2
            + counts["culture"] * 1.5 + counts["health"] * 1.5
            - counts["pressure"] * 2.6,
            12, 96,
        )
        pressure = clamp(
            10 + counts["pressure"] * 5.8 + counts["mobility"] * 0.6
            - counts["green_space"] * 0.9 + c * 4,
            4, 98,
        )
        attractiveness = clamp(
            accessibility * 0.55 + counts["green_space"] * 1.4
            + counts["culture"] * 1.0 + counts["housing"] * 0.6
            - pressure * 0.28,
            8, 98,
        )
        score = round((accessibility + attractiveness - pressure * 0.25) / 2)

        rows.append({
            "code": district["code"],
            "name": district["name"],
            "label": district["label"],
            "x": 300 + i * 25,
            "y": 200 + int(math.sin(i) * 100),
            "family_counts": counts,
            "accessibility_index": round(accessibility),
            "pressure_index": round(pressure),
            "attractiveness_index": round(attractiveness),
            "score": score,
        })

    return rows


@lru_cache(maxsize=1)
def city_overview():
    rows = district_rows()
    n = len(rows)
    return {
        "source_count": len(source_catalog()),
        "family_count": len(FAMILIES),
        "district_count": n,
        "accessibility_index": round(sum(r["accessibility_index"] for r in rows) / n),
        "pressure_index": round(sum(r["pressure_index"] for r in rows) / n),
        "attractiveness_index": round(sum(r["attractiveness_index"] for r in rows) / n),
        "source_family_counts": source_family_counts(),
    }


@lru_cache(maxsize=1)
def timeline_rows():
    # 1. Try PostgreSQL
    try:
        from .db import pg_fetch_all
        sql = """
            SELECT 
                year,
                month,
                SUM(record_count) as activity,
                AVG(accessibility_index) as accessibility_index,
                AVG(pressure_index) as pressure_index,
                AVG(attractiveness_index) as attractiveness_index
            FROM fact_arrondissement_timeline
            GROUP BY year, month
            ORDER BY year ASC, month ASC
        """
        db_rows = pg_fetch_all(sql)
        if db_rows:
            rows = []
            for row in db_rows:
                y = int(row["year"])
                m = int(row["month"])
                
                month_str = f"{y:04d}-{m:02d}"
                month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                label_str = f"{month_names[m - 1]} {y}"
                
                rows.append({
                    "month": month_str,
                    "label": label_str,
                    "activity": int(row["activity"]),
                    "accessibility_index": round(float(row["accessibility_index"]), 2),
                    "pressure_index": round(float(row["pressure_index"]), 2),
                    "attractiveness_index": round(float(row["attractiveness_index"]), 2),
                })
            if rows:
                return rows
    except Exception as exc:
        print(f"  [INFO] PostgreSQL timeline_rows failed: {exc}")

    # 2. Try Parquet
    try:
        import polars as pl
        parquet_path = ROOT / "data" / "gold" / "timeline.parquet"
        if parquet_path.exists():
            df = pl.read_parquet(parquet_path)
            agg_df = (
                df.group_by(["year", "month"])
                .agg([
                    pl.col("record_count").sum().alias("activity"),
                    pl.col("accessibility_index").mean().alias("accessibility_index"),
                    pl.col("pressure_index").mean().alias("pressure_index"),
                    pl.col("attractiveness_index").mean().alias("attractiveness_index"),
                ])
                .sort(["year", "month"])
            )
            
            rows = []
            for row in agg_df.to_dicts():
                y = int(row["year"])
                m = int(row["month"])
                month_str = f"{y:04d}-{m:02d}"
                month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                label_str = f"{month_names[m - 1]} {y}"
                
                rows.append({
                    "month": month_str,
                    "label": label_str,
                    "activity": int(row["activity"]),
                    "accessibility_index": round(float(row["accessibility_index"]), 2),
                    "pressure_index": round(float(row["pressure_index"]), 2),
                    "attractiveness_index": round(float(row["attractiveness_index"]), 2),
                })
            if rows:
                return rows
    except Exception as exc:
        print(f"  [INFO] Parquet timeline failed: {exc}")

    # 3. Fallback to math generator
    rows = []
    baseline = city_overview()
    start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=330)

    for i in range(12):
        current = start + timedelta(days=30 * i)
        wave = math.sin(i / 12 * math.tau)
        rows.append({
            "month": current.strftime("%Y-%m"),
            "label": current.strftime("%b %Y"),
            "activity": round(70 + i * 4 + wave * 12),
            "accessibility_index": clamp(baseline["accessibility_index"] + wave * 3, 0, 100),
            "pressure_index": clamp(baseline["pressure_index"] + wave * 2.5, 0, 100),
            "attractiveness_index": clamp(baseline["attractiveness_index"] + wave * 2.75, 0, 100),
        })

    return rows


@lru_cache(maxsize=1)
def recent_events():
    rows = district_rows()
    catalog = source_catalog()
    now = datetime.now(UTC)
    events = []

    for i in range(18):
        district = rows[i % len(rows)]
        source = catalog[i % len(catalog)]
        events.append({
            "event_id": f"ude-{i + 1:03d}",
            "event_type": ["ingest", "dashboard_refresh", "stream_update"][i % 3],
            "source_id": source["source_id"],
            "district_code": district["code"],
            "payload": {
                "family": source["family"],
                "score": district["score"],
                "message": f"{source['title']} agrégé dans {district['label']} {district['name']}",
            },
            "event_time": now - timedelta(minutes=i * 17),
        })

    return events


@lru_cache(maxsize=1)
def latest_pipeline_run():
    rows = district_rows()
    baseline = city_overview()
    return {
        "run_date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "stage": "gold_refresh",
        "status": "ready",
        "row_count": len(rows) * 12,
        "updated_at": datetime.now(UTC),
        "summary": f"{baseline['district_count']} arrondissements prêts",
    }


LEVEL_FILES = {
    0: DATA_DIR / "paris_city.geojson",
    1: DATA_DIR / "paris_arrondissements.geojson",
    2: DATA_DIR / "paris_iris.geojson",
    3: DATA_DIR / "paris_streets.geojson",
    4: DATA_DIR / "paris_buildings.geojson",
}

LEVEL_NAMES = {
    0: "Ville",
    1: "Arrondissement",
    2: "IRIS",
    3: "Rue",
    4: "Bâtiment",
}


@lru_cache(maxsize=5)
def _load_geojson(path: str) -> dict:
    """Charge un fichier GeoJSON depuis le disque (avec cache LRU)."""
    p = Path(path)
    if not p.exists():
        return {"type": "FeatureCollection", "features": []}
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def geojson_by_granularity(level: int) -> dict:
    """Retourne le GeoJSON correspondant au niveau de granularité demandé.

    Levels:
        0 → Ville (Paris)          – paris_city.geojson
        1 → Arrondissement         – paris_arrondissements.geojson
        2 → IRIS (Quartier)        – paris_iris.geojson
        3 → Rue                    – paris_streets.geojson
        4 → Bâtiment               – paris_buildings.geojson
    """
    level = max(0, min(4, int(level)))
    path = LEVEL_FILES.get(level)
    if path is None or not path.exists():
        # Fallback : arrondissements
        path = LEVEL_FILES[1]
    return _load_geojson(str(path))


@lru_cache(maxsize=1)
def iris_geojson() -> dict:
    """Rétro-compatibilité : retourne les arrondissements."""
    return _load_geojson(str(LEVEL_FILES[1]))
