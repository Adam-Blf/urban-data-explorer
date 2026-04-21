"""
Phase Bronze : Ingestion des Données Brutes
Auteur : Arnaud DISSONGO (Panason1c)
Rôle : Extraction automatisée des datasets de l'API OpenData Paris et Data.gouv.fr.
       Stockage au format brut (JSON/CSV) dans la couche Bronze.
"""

import os
import requests
import time
from config import (
    BRONZE_DIR, PARIS_DATASETS, DATA_GOUV_DATASETS, 
    PARIS_OPENDATA_BASE, PARIS_OPENDATA_GEOJSON_BASE
)


def ensure_bronze_dir():
    """Vérifie l'existence du dossier data/bronze ou le crée."""
    if not os.path.exists(BRONZE_DIR):
        os.makedirs(BRONZE_DIR)
        print(f"Creating Bronze directory: {BRONZE_DIR}")

def download_file(url, target_path):
    """
    Télécharge un fichier distant.
    
    Args:
        url (str): L'URL source.
        target_path (str): Le chemin de destination local.
    """
    print(f"Downloading: {url}...")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Success: {target_path} ({(os.path.getsize(target_path) / 1024 / 1024):.2f} MB)")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")

def ingest_all():
    """Orchestre l'ingestion de tous les datasets définis dans la config."""
    ensure_bronze_dir()
    
    total_datasets = len(PARIS_DATASETS) + len(DATA_GOUV_DATASETS)
    print(f"\n--- Starting Bronze Phase Ingestion ({total_datasets} datasets) ---")
    print("=" * 50)
    
    # 1. OpenData Paris
    for name, info in PARIS_DATASETS.items():
        dataset_id = info['id']
        fmt = info['format']
        url = PARIS_OPENDATA_BASE.format(dataset=dataset_id)
        if fmt == "geojson":
            url = PARIS_OPENDATA_GEOJSON_BASE.format(dataset=dataset_id)
            
        target_path = os.path.join(BRONZE_DIR, f"{name}.{fmt}")
        download_file(url, target_path)
        time.sleep(0.2) # Throttling amical
        
    # 2. Data.gouv.fr
    for name, info in DATA_GOUV_DATASETS.items():
        url = info['url']
        fmt = info['format']
        target_path = os.path.join(BRONZE_DIR, f"{name}.{fmt}")
        download_file(url, target_path)

        
    print("\nBronze Ingestion Complete!")

if __name__ == "__main__":
    ingest_all()
