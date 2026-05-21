#!/usr/bin/env python3
"""Telecharge les 5 fichiers GeoJSON (un par niveau de granularite).

Sources (Open Data Paris - API Explore v2.1) :
  Niveau 0 (Ville)          : Calcule a partir des arrondissements (union)
  Niveau 1 (Arrondissements): opendata.paris.fr / dataset "arrondissements"
  Niveau 2 (Quartiers/IRIS) : opendata.paris.fr / dataset "quartier_paris"
  Niveau 3 (Rues)           : opendata.paris.fr / dataset "voie"
  Niveau 4 (Batiments)      : opendata.paris.fr / dataset "plub_surf_pvp"
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "downloads"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT = 180
MAX_RETRIES = 3

# Open Data Paris - Explore API v2.1 export endpoints
DATASETS = {
    "arrondissements": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson?limit=-1",
        "file": "paris_arrondissements.geojson",
        "label": "Arrondissements",
        "level": 1,
    },
    "quartiers": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/quartier_paris/exports/geojson?limit=-1",
        "file": "paris_iris.geojson",
        "label": "Quartiers administratifs (IRIS)",
        "level": 2,
    },
    "voies": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/voie/exports/geojson?limit=-1",
        "file": "paris_streets.geojson",
        "label": "Lineaires des voies",
        "level": 3,
    },
    "batiments": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/plub_surf_pvp/exports/geojson?limit=-1",
        "file": "paris_buildings.geojson",
        "label": "Emprises baties (PLU)",
        "level": 4,
    },
}


def _download(url: str, label: str) -> dict:
    """Download JSON from url with retries."""
    headers = {"User-Agent": "UrbanDataExplorer/1.0", "Accept": "application/json"}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  [{attempt}/{MAX_RETRIES}] Telechargement {label}...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read()
                print(f"  OK - {len(raw) / 1024:.0f} Ko recus")
                return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            print(f"  ERREUR : {exc}")
            if attempt < MAX_RETRIES:
                wait = 5 * attempt
                print(f"    -> Nouvelle tentative dans {wait}s...")
                time.sleep(wait)
    print(f"  ECHEC definitif pour {label}")
    return {"type": "FeatureCollection", "features": []}


def _save(data: dict, filename: str) -> None:
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    size = path.stat().st_size
    n = len(data.get("features", []))
    print(f"  -> Sauvegarde : {filename}  ({n} features, {size / 1024:.0f} Ko)\n")


# -- Niveau 1 : Arrondissements -----------------------------------------------

def download_arrondissements() -> dict:
    print("== Niveau 1 - Arrondissements ==")
    ds = DATASETS["arrondissements"]
    data = _download(ds["url"], ds["label"])

    if not data.get("features"):
        # Fallback: use existing local file
        local = DATA_DIR / "paris_iris.geojson"
        if local.exists():
            print("  FALLBACK : utilisation du fichier local existant")
            with open(local, encoding="utf-8") as fh:
                data = json.load(fh)

    for feat in data.get("features", []):
        props = feat.setdefault("properties", {})
        props["level"] = 1

    _save(data, ds["file"])
    return data


# -- Niveau 0 : Ville (Paris) -------------------------------------------------

def generate_city(arrondissements: dict) -> dict:
    """Merge all arrondissement polygons into a single MultiPolygon."""
    print("== Niveau 0 - Ville de Paris ==")
    all_coords = []
    for feat in arrondissements.get("features", []):
        geom = feat.get("geometry", {})
        gtype = geom.get("type", "")
        coords = geom.get("coordinates", [])
        if gtype == "Polygon":
            all_coords.append(coords)
        elif gtype == "MultiPolygon":
            all_coords.extend(coords)

    city = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": all_coords,
                },
                "properties": {
                    "name": "Paris",
                    "label": "Ville de Paris",
                    "level": 0,
                    "population": 2133111,
                    "surface_km2": 105.4,
                },
            }
        ],
    }
    _save(city, "paris_city.geojson")
    return city


# -- Niveau 2 : Quartiers administratifs (IRIS) --------------------------------

def download_quartiers() -> dict:
    print("== Niveau 2 - Quartiers administratifs (IRIS) ==")
    ds = DATASETS["quartiers"]
    data = _download(ds["url"], ds["label"])
    for feat in data.get("features", []):
        feat.setdefault("properties", {})["level"] = 2
    _save(data, ds["file"])
    return data


# -- Niveau 3 : Rues / Voies ---------------------------------------------------

def download_streets() -> dict:
    print("== Niveau 3 - Rues (Voies) ==")
    ds = DATASETS["voies"]
    data = _download(ds["url"], ds["label"])
    for feat in data.get("features", []):
        feat.setdefault("properties", {})["level"] = 3
    _save(data, ds["file"])
    return data


# -- Niveau 4 : Batiments (emprises PLU) ---------------------------------------

def download_buildings() -> dict:
    print("== Niveau 4 - Batiments (emprises PLU) ==")
    ds = DATASETS["batiments"]
    data = _download(ds["url"], ds["label"])
    features = data.get("features", [])

    # The PLU dataset can be large -- sample if needed
    if len(features) > 5000:
        print(f"  INFO: {len(features)} features, echantillonnage a ~5000...")
        step = max(1, len(features) // 5000)
        features = features[::step]
        data["features"] = features
        print(f"  -> Reduit a {len(features)} batiments")

    for feat in features:
        feat.setdefault("properties", {})["level"] = 4

    _save(data, ds["file"])
    return data


# -- Main ----------------------------------------------------------------------

def main():
    print("=" * 52)
    print("  Urban Data Explorer - GeoJSON Multi-Niveaux")
    print("  Sources : opendata.paris.fr (Open Data Paris)")
    print("=" * 52 + "\n")

    # 1) Arrondissements (needed for city generation)
    arrondissements = download_arrondissements()

    # 2) City (generated from arrondissements)
    generate_city(arrondissements)

    # 3) Quartiers (IRIS equivalent)
    download_quartiers()

    # 4) Streets
    download_streets()

    # 5) Buildings
    download_buildings()

    print("=" * 52)
    print("  RESUME")
    print("=" * 52)

    all_ok = True
    for name in [
        "paris_city.geojson",
        "paris_arrondissements.geojson",
        "paris_iris.geojson",
        "paris_streets.geojson",
        "paris_buildings.geojson",
    ]:
        path = DATA_DIR / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            n = len(d.get("features", []))
            if n == 0:
                all_ok = False
                status = "VIDE"
            else:
                status = "OK"
            print(f"  [{status:>4s}] {name:<35s} {n:>6d} features   {path.stat().st_size / 1024:>8.0f} Ko")
        else:
            all_ok = False
            print(f"  [MANQ] {name:<35s}")

    if all_ok:
        print("\n  -> Tous les fichiers sont prets !")
    else:
        print("\n  -> ATTENTION : certains fichiers manquent ou sont vides.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
