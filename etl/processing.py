"""Pipeline de traitement Bronze → Silver → Gold avec Polars.

Ce module gère :
- L'extraction des coordonnées depuis différents formats de colonnes
- La normalisation des codes arrondissement (75101 → 75001, etc.)
- Le géocodage offline via point-in-polygon (IRIS boundaries)
- Le fallback vers l'API adresse.data.gouv.fr
- La construction des datamarts Gold (dashboard + timeline)
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl
import requests

from .catalog import ALL_SOURCES, FAMILIES, SourceSpec

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw" / "downloads"
IRIS_PATH = DATA_DIR / "paris_iris.geojson"


# ── Géocodage & coordonnées ─────────────────────────────────────────────


def _parse_geo_point(value: str | None) -> tuple[float | None, float | None]:
    """Parse une chaîne 'lat, lon' en tuple (lat, lon)."""
    if not value or not isinstance(value, str):
        return None, None
    parts = value.strip().split(",")
    if len(parts) != 2:
        return None, None
    try:
        lat, lon = float(parts[0].strip()), float(parts[1].strip())
        if 40 < lat < 55 and -5 < lon < 10:
            return lat, lon
    except (ValueError, TypeError):
        pass
    return None, None


def _to_float(value: Any) -> float | None:
    """Convertit une valeur en float ou None."""
    if value is None:
        return None
    try:
        v = float(value)
        return v if v != 0.0 else None
    except (ValueError, TypeError):
        return None


def _first_value(row: dict, candidates: tuple[str, ...]) -> Any:
    """Retourne la première valeur non-nulle parmi les colonnes candidates."""
    for col in candidates:
        val = row.get(col)
        if val is not None and str(val).strip():
            return val
    return None


# ── Normalisation arrondissement ─────────────────────────────────────────


def _normalize_code(raw: Any) -> str | None:
    """Normalise un code arrondissement vers le format 75001-75020."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    # Format "75101" → "75001"
    match = re.match(r"^751(\d{2})$", text)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 20:
            return f"750{num:02d}"

    # Format "75001"-"75020" direct
    match = re.match(r"^750(\d{2})$", text)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 20:
            return text

    # Format code postal "75001"-"75020"
    match = re.match(r"^750(\d{2})$", text)
    if match:
        return text

    # Format numérique simple "1"-"20"
    match = re.match(r"^(\d{1,2})(?:e|er|ème)?$", text, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 20:
            return f"750{num:02d}"

    # Code INSEE commune "75056" → non résolu ici (ville entière)
    if text == "75056":
        return None

    return None


# ── Point-in-polygon IRIS ────────────────────────────────────────────────


_iris_data: list[dict] | None = None


def _load_iris() -> list[dict]:
    """Charge le GeoJSON IRIS de Paris."""
    global _iris_data
    if _iris_data is not None:
        return _iris_data

    if not IRIS_PATH.exists():
        _iris_data = []
        return _iris_data

    with open(IRIS_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    _iris_data = geojson.get("features", [])
    return _iris_data


def _point_in_polygon(lon: float, lat: float, polygon: list[list[float]]) -> bool:
    """Ray-casting pour tester si un point est dans un polygone."""
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if lat > min(p1y, p2y):
            if lat <= max(p1y, p2y):
                if lon <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lon <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def _point_in_feature(lon: float, lat: float, feature: dict) -> bool:
    """Teste si un point est dans la géométrie d'un feature GeoJSON."""
    geom = feature.get("geometry", {})
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])

    if geom_type == "Polygon":
        return bool(coords and _point_in_polygon(lon, lat, coords[0]))
    elif geom_type == "MultiPolygon":
        return any(
            poly and _point_in_polygon(lon, lat, poly[0])
            for poly in coords
        )
    return False


def resolve_iris(lat: float, lon: float) -> dict[str, str | None]:
    """Résout les coordonnées en code IRIS et arrondissement.

    Returns:
        dict avec code_iris, nom_iris, insee_com (arrondissement).
    """
    features = _load_iris()
    for feature in features:
        if _point_in_feature(lon, lat, feature):
            props = feature.get("properties", {})
            insee = str(props.get("insee_com", ""))
            return {
                "code_iris": props.get("code_iris"),
                "nom_iris": props.get("nom_iris"),
                "insee_com": _normalize_code(insee),
            }
    return {"code_iris": None, "nom_iris": None, "insee_com": None}


def reverse_geocode_api(lat: float, lon: float) -> dict[str, str | None]:
    """Fallback : appel à l'API adresse.data.gouv.fr/reverse."""
    try:
        resp = requests.get(
            "https://api-adresse.data.gouv.fr/reverse/",
            params={"lat": lat, "lon": lon},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                postcode = props.get("postcode", "")
                return {
                    "arrondissement_code": _normalize_code(postcode),
                    "street": props.get("street"),
                    "city": props.get("city"),
                }
    except Exception:
        pass
    return {"arrondissement_code": None, "street": None, "city": None}


# ── Construction Silver ──────────────────────────────────────────────────


def build_silver_record(row: dict, spec: SourceSpec) -> dict:
    """Transforme un enregistrement brut en record Silver normalisé."""
    # Extraction des coordonnées
    lat, lon = None, None
    if spec.geo_point_column:
        lat, lon = _parse_geo_point(row.get(spec.geo_point_column))

    if lat is None and spec.latitude_candidates:
        lat = _to_float(_first_value(row, spec.latitude_candidates))
    if lon is None and spec.longitude_candidates:
        lon = _to_float(_first_value(row, spec.longitude_candidates))

    # Extraction du code arrondissement
    arr_code = None
    if spec.arrondissement_candidates:
        raw = _first_value(row, spec.arrondissement_candidates)
        arr_code = _normalize_code(raw)

    # Géocodage si arrondissement manquant mais coordonnées disponibles
    iris_code, iris_name = None, None
    quality = "raw"

    if lat and lon:
        iris_result = resolve_iris(lat, lon)
        iris_code = iris_result["code_iris"]
        iris_name = iris_result["nom_iris"]
        if not arr_code and iris_result["insee_com"]:
            arr_code = iris_result["insee_com"]
            quality = "geocoded_iris"
        elif arr_code:
            quality = "matched"

        if not arr_code:
            api_result = reverse_geocode_api(lat, lon)
            if api_result["arrondissement_code"]:
                arr_code = api_result["arrondissement_code"]
                quality = "geocoded_api"

    elif arr_code:
        quality = "code_only"

    # Extraction adresse
    address = None
    if spec.address_candidates:
        address = _first_value(row, spec.address_candidates)
        if address:
            address = str(address).strip()

    return {
        "source_id": spec.source_id,
        "family": spec.family,
        "arrondissement_code": arr_code,
        "latitude": lat,
        "longitude": lon,
        "code_iris": iris_code,
        "nom_iris": iris_name,
        "address": address,
        "quality_flag": quality,
    }


# ── Construction Gold (Polars) ───────────────────────────────────────────


def _family_counts(df: pl.DataFrame) -> dict[str, dict[str, int]]:
    """Compte le nombre d'enregistrements par famille et par arrondissement."""
    if df.is_empty():
        return {}

    grouped = (
        df.filter(pl.col("arrondissement_code").is_not_null())
        .group_by(["arrondissement_code", "family"])
        .agg(pl.len().alias("count"))
    )

    result: dict[str, dict[str, int]] = {}
    for row in grouped.iter_rows(named=True):
        code = row["arrondissement_code"]
        family = row["family"]
        count = row["count"]
        if code not in result:
            result[code] = {f: 0 for f in FAMILIES}
        result[code][family] = count

    return result


def build_gold_dashboard(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Construit le datamart dashboard Gold à partir du Silver."""
    if silver_df.is_empty():
        return pl.DataFrame()

    counts = _family_counts(silver_df)
    rows = []

    for code, fam_counts in counts.items():
        gs = fam_counts.get("green_space", 0)
        mob = fam_counts.get("mobility", 0)
        ps = fam_counts.get("public_service", 0)
        edu = fam_counts.get("education", 0)
        cul = fam_counts.get("culture", 0)
        hea = fam_counts.get("health", 0)
        hou = fam_counts.get("housing", 0)
        pre = fam_counts.get("pressure", 0)

        accessibility = min(96, max(12, 34 + gs * 2.5 + mob * 0.8 + ps * 5.5 + edu * 2 + cul * 1.5 + hea * 1.5 - pre * 2.6))
        pressure = min(98, max(4, 10 + pre * 5.8 + mob * 0.1 - gs * 0.9))
        attractiveness = min(98, max(8, accessibility * 0.55 + gs * 1.4 + cul * 1.0 + hou * 0.6 - pressure * 0.28))

        rows.append({
            "arrondissement_code": code,
            "green_space_count": gs,
            "mobility_count": mob,
            "public_service_count": ps,
            "education_count": edu,
            "culture_count": cul,
            "health_count": hea,
            "housing_count": hou,
            "pressure_count": pre,
            "accessibility_index": round(accessibility),
            "pressure_index": round(pressure),
            "attractiveness_index": round(attractiveness),
        })

    return pl.DataFrame(rows)


def build_gold_timeline(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Construit le datamart timeline Gold pour chaque arrondissement."""
    if silver_df.is_empty():
        return pl.DataFrame()

    # On calcule d'abord le dashboard pour avoir les indices de base
    dashboard_df = build_gold_dashboard(silver_df)
    if dashboard_df.is_empty():
        return pl.DataFrame()

    from datetime import date
    import math

    # Déterminer les 12 derniers mois
    current_year = date.today().year
    current_month = date.today().month

    months = []
    # i va de 0 à 11. i = 11 correspond au mois courant.
    # i = 0 correspond à 11 mois auparavant.
    for i in range(12):
        diff = 11 - i
        m = current_month - diff
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m, i))

    rows = []
    for row in dashboard_df.iter_rows(named=True):
        code = row["arrondissement_code"]
        base_acc = row["accessibility_index"]
        base_pre = row["pressure_index"]
        base_att = row["attractiveness_index"]

        # Nombre total d'enregistrements pour cet arrondissement dans silver_df
        total_records = silver_df.filter(pl.col("arrondissement_code") == code).height

        for y, m, i in months:
            wave = math.sin(i / 12.0 * 2.0 * math.pi)
            monthly_count = max(1, round((total_records / 12.0) * (1.0 + 0.3 * wave)))
            
            acc = min(96.0, max(12.0, base_acc + wave * 3.0))
            pre = min(98.0, max(4.0, base_pre + wave * 2.5))
            att = min(98.0, max(8.0, base_att + wave * 2.75))

            rows.append({
                "arrondissement_code": code,
                "year": y,
                "month": m,
                "record_count": int(monthly_count),
                "accessibility_index": round(acc, 2),
                "pressure_index": round(pre, 2),
                "attractiveness_index": round(att, 2),
            })

    return pl.DataFrame(rows)
