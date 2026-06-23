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
from etl.processing import (
    LOGEMENT_SOCIAL_COUNT_BASES,
    LOGEMENT_SOCIAL_PCT_BASES,
    PRIX_M2_BASES,
    REVENU_MEDIAN_BASES,
    SALES_VOLUME_BASES,
    _normalize_code,
    resolve_iris,
)

@lru_cache(maxsize=10000)
def cached_resolve_iris(lat: float, lon: float) -> str | None:
    res = resolve_iris(lat, lon)
    return res.get("insee_com")

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

# Imported from etl.processing (single source of truth)
# PRIX_M2_BASES, SALES_VOLUME_BASES, REVENU_MEDIAN_BASES,
# LOGEMENT_SOCIAL_PCT_BASES, LOGEMENT_SOCIAL_COUNT_BASES


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


def _enrich_district_row(code: str, raw_row: dict) -> dict:
    """Enrichit un arrondissement avec les indices calculés.

    Utilise les valeurs réelles issues du parquet Gold ou de la DB (prix_m2,
    revenu_median, data_source…) si elles sont présentes dans raw_row et
    positives ; retombe sur les constantes de référence uniquement si absent/nul.
    """
    env = int(raw_row.get("environnement_count", 0))
    mob = int(raw_row.get("mobilite_count", 0))
    vq = int(raw_row.get("vie_quotidienne_count", 0))
    lu = int(raw_row.get("logement_urbanisme_count", 0))

    acc = raw_row.get("accessibility_index", 50)
    press = raw_row.get("pressure_index", 50)
    attr = raw_row.get("attractiveness_index", 50)

    # Utilise les valeurs réelles si présentes et positives, sinon constantes de référence
    def _pos(key: str, default: float) -> float:
        try:
            v = float(raw_row.get(key) or 0)
            return v if v > 0 else default
        except (TypeError, ValueError):
            return default

    prix_m2 = _pos("prix_m2", PRIX_M2_BASES.get(code, 10000.0))
    sales_volume = int(_pos("sales_volume", SALES_VOLUME_BASES.get(code, 300)))
    revenu_median = _pos("revenu_median", REVENU_MEDIAN_BASES.get(code, 30000.0))
    logements_sociaux_count = int(_pos("logements_sociaux_count", LOGEMENT_SOCIAL_COUNT_BASES.get(code, 5000)))
    logement_social_pct = _pos("logement_social_pct", LOGEMENT_SOCIAL_PCT_BASES.get(code, 15.0))
    data_source = raw_row.get("data_source") or "reference"

    # Calcul des indices
    immobilier_idx = round(clamp((prix_m2 - 8000) / (16000 - 8000) * 100, 10, 95))
    logement_social_idx = round(clamp(logement_social_pct * 2.5, 5, 95))
    revenu_idx = round(clamp((revenu_median - 20000) / (48000 - 20000) * 100, 10, 95))
    cadre_vie_idx = round(clamp(acc, 0, 100))
    environnement_idx = round(clamp(env * 7.5, 20, 95))

    # Accessibilité au logement : m² achetables avec un an de revenu médian
    m2_abordables = round(revenu_median / prix_m2, 2) if prix_m2 else 0.0
    accessibilite_idx = round(clamp(m2_abordables / 4.0 * 100, 0, 100))

    # Score global = moyenne des 5 indices
    score = round((immobilier_idx + logement_social_idx + revenu_idx + cadre_vie_idx + environnement_idx) / 5)

    return {
        "code": code,
        "name": raw_row["name"],
        "label": raw_row["label"],
        "x": raw_row.get("x", 0),
        "y": raw_row.get("y", 0),
        "family_counts": {
            "environnement": env,
            "mobilite": mob,
            "vie_quotidienne": vq,
            "logement_urbanisme": lu,
        },
        "accessibility_index": round(acc),
        "pressure_index": round(press),
        "attractiveness_index": round(attr),
        "score": score,
        "immobilier_idx": immobilier_idx,
        "logement_social_idx": logement_social_idx,
        "revenu_idx": revenu_idx,
        "cadre_vie_idx": cadre_vie_idx,
        "environnement_idx": environnement_idx,
        "prix_m2": prix_m2,
        "logements_sociaux_count": logements_sociaux_count,
        "logement_social_pct": logement_social_pct,
        "revenu_median": revenu_median,
        "sales_volume": sales_volume,
        "m2_abordables": m2_abordables,
        "accessibilite_idx": accessibilite_idx,
        "data_source": data_source,
    }


@lru_cache(maxsize=1)
def district_rows():
    # 1. Try PostgreSQL
    try:
        from .db import pg_fetch_all
        sql = """
            SELECT
                arrondissement_code,
                environnement_count,
                mobilite_count,
                vie_quotidienne_count,
                logement_urbanisme_count,
                accessibility_index,
                pressure_index,
                attractiveness_index,
                prix_m2,
                revenu_median,
                sales_volume,
                logements_sociaux_count,
                logement_social_pct,
                COALESCE(data_source, 'reference') AS data_source
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

                raw_row = {
                    "name": district["name"],
                    "label": district["label"],
                    "x": 300 + i * 25,
                    "y": 200 + int(math.sin(i) * 100),
                    "environnement_count": row["environnement_count"],
                    "mobilite_count": row["mobilite_count"],
                    "vie_quotidienne_count": row["vie_quotidienne_count"],
                    "logement_urbanisme_count": row["logement_urbanisme_count"],
                    "accessibility_index": row["accessibility_index"],
                    "pressure_index": row["pressure_index"],
                    "attractiveness_index": row["attractiveness_index"],
                    "prix_m2": row.get("prix_m2"),
                    "revenu_median": row.get("revenu_median"),
                    "sales_volume": row.get("sales_volume"),
                    "logements_sociaux_count": row.get("logements_sociaux_count"),
                    "logement_social_pct": row.get("logement_social_pct"),
                    "data_source": row.get("data_source"),
                }
                rows.append(_enrich_district_row(code, raw_row))

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

                raw_row = {
                    "name": district["name"],
                    "label": district["label"],
                    "x": 300 + i * 25,
                    "y": 200 + int(math.sin(i) * 100),
                    "environnement_count": row.get("environnement_count", 0),
                    "mobilite_count": row.get("mobilite_count", 0),
                    "vie_quotidienne_count": row.get("vie_quotidienne_count", 0),
                    "logement_urbanisme_count": row.get("logement_urbanisme_count", 0),
                    "accessibility_index": row["accessibility_index"],
                    "pressure_index": row["pressure_index"],
                    "attractiveness_index": row["attractiveness_index"],
                    "prix_m2": row.get("prix_m2"),
                    "revenu_median": row.get("revenu_median"),
                    "sales_volume": row.get("sales_volume"),
                    "logements_sociaux_count": row.get("logements_sociaux_count"),
                    "logement_social_pct": row.get("logement_social_pct"),
                    "data_source": row.get("data_source"),
                }
                rows.append(_enrich_district_row(code, raw_row))
            
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
            if family == "environnement":
                base = 2 + round((1 - c) * 5) + round(fb * 2) + density // 4
            elif family == "mobilite":
                base = 3 + round((0.6 + bias) * 4) + density // 3
            elif family == "vie_quotidienne":
                base = 2 + round((0.35 + c) * 5) + density // 4
            counts[family] = max(0, base)

        env = counts["environnement"]
        mob = counts["mobilite"]
        vq = counts["vie_quotidienne"]
        lu = counts["logement_urbanisme"]

        accessibility = clamp(34 + env * 2.5 + mob * 0.8 + vq * 1.5 - lu * 0.3, 12, 96)
        pressure = clamp(10 + lu * 1.5 + mob * 0.1 - env * 0.9, 4, 98)
        attractiveness = clamp(accessibility * 0.55 + env * 1.4 + vq * 1.0 + lu * 0.6 - pressure * 0.28, 8, 98)

        raw_row = {
            "name": district["name"],
            "label": district["label"],
            "x": 300 + i * 25,
            "y": 200 + int(math.sin(i) * 100),
            "environnement_count": env,
            "mobilite_count": mob,
            "vie_quotidienne_count": vq,
            "logement_urbanisme_count": lu,
            "accessibility_index": accessibility,
            "pressure_index": pressure,
            "attractiveness_index": attractiveness,
        }
        rows.append(_enrich_district_row(district["code"], raw_row))

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
        "immobilier_idx": round(sum(r["immobilier_idx"] for r in rows) / n),
        "logement_social_idx": round(sum(r["logement_social_idx"] for r in rows) / n),
        "revenu_idx": round(sum(r["revenu_idx"] for r in rows) / n),
        "cadre_vie_idx": round(sum(r["cadre_vie_idx"] for r in rows) / n),
        "environnement_idx": round(sum(r["environnement_idx"] for r in rows) / n),
        "prix_m2": round(sum(r["prix_m2"] for r in rows) / n, 2),
        "logement_social_pct": round(sum(r["logement_social_pct"] for r in rows) / n, 2),
        "revenu_median": round(sum(r["revenu_median"] for r in rows) / n, 2),
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
                
                wave = math.sin((m - 1) / 12.0 * 2.0 * math.pi)
                acc = float(row["accessibility_index"])
                
                rows.append({
                    "month": month_str,
                    "label": label_str,
                    "activity": int(row["activity"]),
                    "accessibility_index": round(acc, 2),
                    "pressure_index": round(float(row["pressure_index"]), 2),
                    "attractiveness_index": round(float(row["attractiveness_index"]), 2),
                    "immobilier_idx": round(clamp(60.0 + wave * 2.0, 0, 100), 2),
                    "logement_social_idx": round(clamp(15.0 + wave * 0.5, 0, 100), 2),
                    "revenu_idx": round(clamp(50.0 + wave * 1.5, 0, 100), 2),
                    "cadre_vie_idx": round(clamp(acc, 0, 100), 2),
                    "environnement_idx": round(clamp(70.0 + wave * 2.2, 0, 100), 2),
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
                
                wave = math.sin((m - 1) / 12.0 * 2.0 * math.pi)
                acc = float(row["accessibility_index"])
                
                rows.append({
                    "month": month_str,
                    "label": label_str,
                    "activity": int(row["activity"]),
                    "accessibility_index": round(float(row["accessibility_index"]), 2),
                    "pressure_index": round(float(row["pressure_index"]), 2),
                    "attractiveness_index": round(float(row["attractiveness_index"]), 2),
                    "immobilier_idx": round(clamp(60.0 + wave * 2.0, 0, 100), 2),
                    "logement_social_idx": round(clamp(15.0 + wave * 0.5, 0, 100), 2),
                    "revenu_idx": round(clamp(50.0 + wave * 1.5, 0, 100), 2),
                    "cadre_vie_idx": round(clamp(acc, 0, 100), 2),
                    "environnement_idx": round(clamp(70.0 + wave * 2.2, 0, 100), 2),
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
            "immobilier_idx": round(clamp(baseline["immobilier_idx"] + wave * 2.0, 0, 100), 2),
            "logement_social_idx": round(clamp(baseline["logement_social_idx"] + wave * 0.5, 0, 100), 2),
            "revenu_idx": round(clamp(baseline["revenu_idx"] + wave * 1.5, 0, 100), 2),
            "cadre_vie_idx": round(clamp(baseline["cadre_vie_idx"] + wave * 3.0, 0, 100), 2),
            "environnement_idx": round(clamp(baseline["environnement_idx"] + wave * 2.5, 0, 100), 2),
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
    """Retourne le GeoJSON correspondant au niveau de granularité demandé,
    enrichi avec les métriques et indices calculés.

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
        path = LEVEL_FILES[1]
        
    geojson = _load_geojson(str(path))
    
    # Enrichir avec les indicateurs
    try:
        districts = district_rows()
        dist_map = {d["code"]: d for d in districts}
        
        # Modifier en place
        for feature in geojson.get("features", []):
            properties = feature.get("properties", {})
            if not properties:
                continue
                
            code = None
            if level == 1:
                code = properties.get("c_arinsee") or properties.get("c_ar") or properties.get("insee_com")
            elif level == 2:
                iris = properties.get("code_iris") or properties.get("c_iris") or properties.get("iris")
                if isinstance(iris, str) and len(iris) >= 5:
                    code = iris[:5]
            elif level == 3:
                geom = properties.get("geom_x_y")
                if isinstance(geom, dict):
                    lon = geom.get("lon")
                    lat = geom.get("lat")
                    if lat is not None and lon is not None:
                        code = cached_resolve_iris(float(lat), float(lon))
            elif level == 4:
                geom = properties.get("geo_point_2d")
                if isinstance(geom, dict):
                    lon = geom.get("lon")
                    lat = geom.get("lat")
                    if lat is not None and lon is not None:
                        code = cached_resolve_iris(float(lat), float(lon))
                    
            if code:
                code_str = _normalize_code(code)
                if code_str and code_str in dist_map:
                    d = dist_map[code_str]
                    properties.update({
                        "score": d["score"],
                        "immobilier_idx": d["immobilier_idx"],
                        "logement_social_idx": d["logement_social_idx"],
                        "revenu_idx": d["revenu_idx"],
                        "cadre_vie_idx": d["cadre_vie_idx"],
                        "environnement_idx": d["environnement_idx"],
                        "prix_m2": d["prix_m2"],
                        "logements_sociaux_count": d["logements_sociaux_count"],
                        "logement_social_pct": d["logement_social_pct"],
                        "revenu_median": d["revenu_median"],
                        "sales_volume": d["sales_volume"],
                    })
    except Exception as e:
        print(f"Error enriching GeoJSON: {e}")
        
    return geojson


@lru_cache(maxsize=1)
def iris_geojson() -> dict:
    """Rétro-compatibilité : retourne les arrondissements."""
    return _load_geojson(str(LEVEL_FILES[1]))
