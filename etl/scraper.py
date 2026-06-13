"""
Module de scraping et d'ingestion via API pour l'automatisation du téléchargement
des jeux de données de l'Open Data Paris.
"""

import logging
import requests
from pathlib import Path
from typing import Dict, Any

from etl.catalog import SourceSpec

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def download_dataset(spec: SourceSpec, download_dir: Path) -> bool:
    """
    Télécharge le fichier CSV d'un jeu de données depuis l'API Open Data Paris.

    Args:
        spec: Spécification de la source de données.
        download_dir: Répertoire de destination pour le fichier CSV.

    Returns:
        True si le téléchargement a réussi, False sinon.
    """
    try:
        # Extraire le dataset_id de l'URL du catalogue
        # Exemple: https://opendata.paris.fr/explore/dataset/logements-sociaux-finances-a-paris/
        url_parts = spec.catalog_url.rstrip("/").split("/dataset/")
        if len(url_parts) < 2:
            logger.error(f"URL de catalogue invalide : {spec.catalog_url}")
            return False
        
        dataset_id = url_parts[-1]
        base_url = url_parts[0].split("/explore")[0]
        csv_link = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv?limit=-1"

        if spec.source_id == "transit_stops":
            csv_link += "&where=arrpostalregion%20like%20%27751*%27"

        # Le fichier de destination
        file_path = download_dir / f"{spec.source_id}.csv"
        
        logger.info(f"Téléchargement du dataset {spec.source_id} depuis : {csv_link}")

        # Téléchargement effectif du fichier
        response = requests.get(csv_link, timeout=60, stream=True)
        response.raise_for_status()

        # Sauvegarde du fichier
        download_dir.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"Fichier sauvegardé avec succès : {file_path}")
        return True

    except Exception as e:
        logger.exception(f"Erreur lors du téléchargement de {spec.source_id}: {e}")
        return False

def scrape_catalog_metadata(spec: SourceSpec) -> Dict[str, Any]:
    """
    Extrait les métadonnées clés d'une page de jeu de données via l'API Open Data Paris.

    Args:
        spec: Spécification de la source de données.

    Returns:
        Un dictionnaire contenant le titre, la description et la date de mise à jour.
    """
    try:
        url_parts = spec.catalog_url.rstrip("/").split("/dataset/")
        if len(url_parts) < 2:
            return {
                "title": spec.title,
                "description": "URL de catalogue invalide",
                "last_update": "Inconnue"
            }
        
        dataset_id = url_parts[-1]
        base_url = url_parts[0].split("/explore")[0]
        api_url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}"
        
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            metas = data.get("metas", {}).get("default", {})
            title = metas.get("title", spec.title)
            description = metas.get("description", "Non disponible")
            last_update = metas.get("modified", "Inconnue")
            return {
                "title": title,
                "description": description,
                "last_update": last_update
            }
        
        return {
            "title": spec.title,
            "description": "Jeu de données introuvable sur l'API",
            "last_update": "Inconnue"
        }

    except Exception as e:
        logger.warning(f"Impossible d'extraire les métadonnées pour {spec.source_id}: {e}")
        return {
            "title": spec.title,
            "description": "Erreur d'extraction via l'API",
            "last_update": "Inconnue"
        }
