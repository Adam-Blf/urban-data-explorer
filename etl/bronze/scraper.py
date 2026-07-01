"""Scraping et téléchargement des sources Open Data Paris."""

import logging
import requests
from pathlib import Path
from typing import Any

from .catalog import SourceSpec

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def download_dataset(spec: SourceSpec, download_dir: Path) -> bool:
    """Télécharge le fichier CSV d'une source via spec.download_url."""
    url = spec.download_url
    if not url:
        logger.warning(f"Pas de download_url pour {spec.source_id} - ignore")
        return False

    # Les sources Overpass sont gérées par auto_ingest, pas ici
    if url.startswith("OVERPASS:"):
        return False

    ext = ".csv.gz" if url.endswith(".csv.gz") else ".csv"
    file_path = download_dir / f"{spec.source_id}{ext}"
    download_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Téléchargement {spec.source_id} depuis : {url}")
    try:
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        logger.info(f"Sauvegardé : {file_path}")
        return True
    except Exception as exc:
        logger.exception(f"Erreur téléchargement {spec.source_id}: {exc}")
        return False


def scrape_catalog_metadata(spec: SourceSpec) -> dict[str, Any]:
    """Extrait les métadonnées depuis l'API Opendatasoft."""
    try:
        parts = spec.catalog_url.rstrip("/").split("/dataset/")
        if len(parts) < 2:
            return {"title": spec.title, "description": "URL invalide", "last_update": "Inconnue"}
        dataset_id = parts[-1]
        base_url = parts[0].split("/explore")[0]
        api_url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}"
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            metas = r.json().get("metas", {}).get("default", {})
            return {
                "title": metas.get("title", spec.title),
                "description": metas.get("description", "Non disponible"),
                "last_update": metas.get("modified", "Inconnue"),
            }
    except Exception as exc:
        logger.warning(f"Métadonnées {spec.source_id}: {exc}")
    return {"title": spec.title, "description": "Erreur API", "last_update": "Inconnue"}
