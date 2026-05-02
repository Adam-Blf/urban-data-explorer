"""Source · GeoJSON des 20 arrondissements de Paris (OpenData Paris).

Le fichier brut est gardé tel quel dans /raw, et reconverti par le silver
en `polars.DataFrame` (centroïde + bbox + code arrondissement).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx


def fetch(
    raw_partition_dir: Path,
    geojson_url: str,
    logger: logging.Logger,
) -> Path:
    """Télécharge le GeoJSON arrondissements et le persiste tel quel."""
    raw_partition_dir.mkdir(parents=True, exist_ok=True)
    out = raw_partition_dir / "arrondissements.geojson"

    logger.info("arrondissements · downloading %s", geojson_url)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        resp = client.get(geojson_url)
        resp.raise_for_status()
        payload = resp.json()

    feature_count = len(payload.get("features", []))
    if feature_count == 0:
        logger.error("arrondissements · empty GeoJSON · using local fallback")
        payload = _fallback_geojson()

    out.write_text(json.dumps(payload), encoding="utf-8")
    logger.info(
        "arrondissements · wrote %s (%d features)",
        out,
        len(payload["features"]),
    )
    return out


def _fallback_geojson() -> dict:
    """Bbox approximatives par arrondissement (utile si OpenData down)."""
    centers = [
        (75101, 2.337, 48.862), (75102, 2.347, 48.868), (75103, 2.362, 48.863),
        (75104, 2.357, 48.854), (75105, 2.350, 48.844), (75106, 2.333, 48.849),
        (75107, 2.312, 48.856), (75108, 2.318, 48.872), (75109, 2.337, 48.877),
        (75110, 2.361, 48.876), (75111, 2.380, 48.859), (75112, 2.421, 48.835),
        (75113, 2.362, 48.829), (75114, 2.327, 48.829), (75115, 2.300, 48.840),
        (75116, 2.262, 48.860), (75117, 2.307, 48.887), (75118, 2.349, 48.892),
        (75119, 2.385, 48.887), (75120, 2.401, 48.863),
    ]
    features = []
    for code, lon, lat in centers:
        features.append({
            "type": "Feature",
            "properties": {
                "c_ar": int(str(code)[-2:]),
                "code_arrondissement": str(code),
                "l_ar": f"{int(str(code)[-2:])}e arrondissement",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - 0.012, lat - 0.008],
                    [lon + 0.012, lat - 0.008],
                    [lon + 0.012, lat + 0.008],
                    [lon - 0.012, lat + 0.008],
                    [lon - 0.012, lat - 0.008],
                ]],
            },
        })
    return {"type": "FeatureCollection", "features": features}
