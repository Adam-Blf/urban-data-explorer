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
PARIS_GEOJSON_PATH = DATA_DIR / "paris_iris.geojson"

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


@lru_cache(maxsize=10)
def geojson_by_granularity(level: int) -> dict:
    """Retourne le GeoJSON correspondant au niveau de granularité demandé.

    Levels:
    0: Ville (Paris)
    1: Arrondissement
    2: IRIS
    3: Rue
    4: Immeuble
    """
    level = max(0, min(4, int(level)))
    collection = iris_geojson()

    if level == 0:
        return _city_geojson(collection)

    return collection


@lru_cache(maxsize=1)
def iris_geojson() -> dict:
    with PARIS_GEOJSON_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _city_geojson(collection: dict) -> dict:
    bounds = None

    for feature in collection.get("features", []):
        feature_bounds = _feature_bounds(feature)
        if feature_bounds is None:
            continue
        if bounds is None:
            bounds = feature_bounds
            continue

        bounds = (
            min(bounds[0], feature_bounds[0]),
            min(bounds[1], feature_bounds[1]),
            max(bounds[2], feature_bounds[2]),
            max(bounds[3], feature_bounds[3]),
        )

    if bounds is None:
        return {"type": "FeatureCollection", "features": []}

    min_lon, min_lat, max_lon, max_lat = bounds
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat],
                        [max_lon, min_lat],
                        [max_lon, max_lat],
                        [min_lon, max_lat],
                        [min_lon, min_lat],
                    ]],
                },
                "properties": {
                    "name": "Paris",
                    "label": "Ville",
                    "level": 0,
                },
            }
        ],
    }


def _feature_bounds(feature: dict) -> tuple[float, float, float, float] | None:
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    if not coordinates:
        return None

    points: list[tuple[float, float]] = []

    def collect(coords):
        if isinstance(coords, list) and coords and isinstance(coords[0], (int, float)):
            points.append((float(coords[0]), float(coords[1])))
            return
        for item in coords or []:
            collect(item)

    collect(coordinates)
    if not points:
        return None

    lons = [point[0] for point in points]
    lats = [point[1] for point in points]
    return min(lons), min(lats), max(lons), max(lats)
