"""
Couche Bronze (medallion architecture).

Rôle : télécharger les données brutes depuis les APIs publiques et les stocker
telles quelles (aucune transformation), une copie horodatée par jour. Un fichier
manquant/404 n'interrompt pas la pipeline · il est simplement logué.

Chemin de sortie : data/bronze/<source>/<YYYY-MM-DD>.<ext>
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
import requests

BRONZE = Path(__file__).resolve().parents[2] / "data" / "bronze"

SOURCES = {
    "arrondissements": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson",
        "ext": "geojson",
    },
    "logements_sociaux": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/logements-sociaux-finances-a-paris/exports/json",
        "ext": "json",
    },
    "espaces_verts": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/espaces_verts/exports/geojson",
        "ext": "geojson",
    },
    "velib_stations": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-emplacement-des-stations/exports/geojson",
        "ext": "geojson",
    },
    "ecoles_elementaires": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/etablissements-scolaires-ecoles-elementaires/exports/geojson",
        "ext": "geojson",
    },
    # Autres équipements urbains, agrégés par arrondissement côté silver
    "colleges": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/etablissements-scolaires-colleges/exports/geojson",
        "ext": "geojson",
    },
    "marches_decouverts": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/marches-decouverts/exports/geojson",
        "ext": "geojson",
    },
    "sanisettes": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/sanisettesparis/exports/geojson",
        "ext": "geojson",
    },
    "belib": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel/exports/geojson",
        "ext": "geojson",
    },
    "amenagements_cyclables": {
        "url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/amenagements-cyclables/exports/geojson",
        "ext": "geojson",
    },
    **{
        f"dvf_{y}": {
            "url": f"https://files.data.gouv.fr/geo-dvf/latest/csv/{y}/departements/75.csv.gz",
            "ext": "csv.gz",
        }
        for y in (2020, 2021, 2022, 2023, 2024)
    },
}


def fetch(name: str, cfg: dict) -> Path:
    """Télécharge une source et la dépose dans data/bronze/<name>/<date>.<ext>."""
    out_dir = BRONZE / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{date.today().isoformat()}.{cfg['ext']}"
    print(f"[bronze] GET {cfg['url']}")
    r = requests.get(cfg["url"], timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"[bronze] wrote {out} ({len(r.content)} bytes)")
    return out


def run() -> dict[str, Path]:
    """Itère sur toutes les sources · échec isolé par source (ne propage pas)."""
    out = {}
    for name, cfg in SOURCES.items():
        try:
            out[name] = fetch(name, cfg)
        except Exception as e:
            print(f"[bronze] SKIP {name}: {e}")
    return out


if __name__ == "__main__":
    run()
