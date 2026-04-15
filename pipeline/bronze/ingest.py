"""Bronze · ingestion brute des sources vers data/bronze/<source>/<date>.ext"""
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
    **{
        f"dvf_{y}": {
            "url": f"https://files.data.gouv.fr/geo-dvf/latest/csv/{y}/departements/75.csv.gz",
            "ext": "csv.gz",
        }
        for y in (2020, 2021, 2022, 2023, 2024)
    },
}


def fetch(name: str, cfg: dict) -> Path:
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
    out = {}
    for name, cfg in SOURCES.items():
        try:
            out[name] = fetch(name, cfg)
        except Exception as e:
            print(f"[bronze] SKIP {name}: {e}")
    return out


if __name__ == "__main__":
    run()
