"""Endpoints géospatiaux · GeoJSON arrondissements + POI filtrables."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from pipeline.config import get_settings

from ..db import gold_connection
from ..security import get_current_user

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/arrondissements.geojson")
def get_arrondissements_geojson(user: str = Depends(get_current_user)):
    """Retourne le GeoJSON enrichi des KPIs arrondissement.

    Priorité · raw GeoJSON ingéré (`arrondissements/...`). Fallback ·
    polygones bbox synthétiques à partir des centroïdes Gold (utile en mode
    démo seed, sans avoir à télécharger le vrai GeoJSON).
    """
    settings = get_settings()
    arr_files = sorted(
        (settings.raw_dir / "arrondissements").rglob("arrondissements.geojson")
    )

    with gold_connection() as con:
        kpi_rows = con.execute("SELECT * FROM kpi_arrondissement").fetch_arrow_table().to_pylist()
    kpi_index = {r["code_arrondissement"]: r for r in kpi_rows}

    if arr_files:
        payload = json.loads(Path(arr_files[-1]).read_text(encoding="utf-8"))
    else:
        # Fallback · bbox synthétique autour de chaque centroïde Gold
        features = []
        for code, kpi in kpi_index.items():
            lon = kpi.get("centroid_lon")
            lat = kpi.get("centroid_lat")
            if lon is None or lat is None:
                continue
            features.append({
                "type": "Feature",
                "properties": {"code_arrondissement": code},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon - 0.014, lat - 0.009],
                        [lon + 0.014, lat - 0.009],
                        [lon + 0.014, lat + 0.009],
                        [lon - 0.014, lat + 0.009],
                        [lon - 0.014, lat - 0.009],
                    ]],
                },
            })
        payload = {"type": "FeatureCollection", "features": features}

    for feat in payload.get("features", []):
        props = feat.setdefault("properties", {})
        code = (
            props.get("code_arrondissement")
            or _normalize(props.get("c_ar"))
            or props.get("c_arinsee")
        )
        props["code_arrondissement"] = code
        if code and code in kpi_index:
            for k, v in kpi_index[code].items():
                if k == "code_arrondissement":
                    continue
                # Coerce DuckDB Decimal / datetime / Arrow scalars to JSON-safe types
                if v is None or isinstance(v, (int, float, str, bool)):
                    props[k] = v
                else:
                    try:
                        props[k] = float(v)
                    except (TypeError, ValueError):
                        props[k] = str(v)
    return JSONResponse(payload)


def _normalize(c) -> str | None:
    if c is None:
        return None
    try:
        return f"751{int(c):02d}"
    except (TypeError, ValueError):
        return None


@router.get("/poi.geojson")
def get_poi_geojson(
    user: str = Depends(get_current_user),
    category: str | None = Query(
        None, description="Filtre par catégorie (transport, sante, culture, ...)"
    ),
    subcategory: str | None = Query(None),
    limit: int = Query(2000, ge=1, le=20_000),
):
    where: list[str] = []
    params: list = []
    if category:
        where.append("category = ?")
        params.append(category)
    if subcategory:
        where.append("subcategory = ?")
        params.append(subcategory)
    where_sql = "WHERE " + " AND ".join(where) if where else ""

    with gold_connection() as con:
        rows = con.execute(
            f"""
            SELECT code_arrondissement, category, subcategory, name, lon, lat
            FROM dim_poi
            {where_sql}
            LIMIT ?
            """,
            [*params, limit],
        ).fetch_arrow_table().to_pylist()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "code_arrondissement": r["code_arrondissement"],
                "category":            r["category"],
                "subcategory":         r["subcategory"],
                "name":                r["name"],
            },
        }
        for r in rows
    ]
    return JSONResponse({"type": "FeatureCollection", "features": features})
