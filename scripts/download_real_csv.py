import urllib.request
import urllib.parse
import json
import time
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = ROOT / "data" / "raw" / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATASET_MAPPING = {
    "logements_sociaux": "logements-sociaux-finances-a-paris",
    "velib_stations": "velib-disponibilite-en-temps-reel",
    "velib_disponibilite": "velib-disponibilite-en-temps-reel",
    "amenagements_cyclables": "amenagements-cyclables",
    "stationnement_voie_publique_emplacements": "stationnement-voie-publique-emplacements",
    "stationnement_voie_publique_emprises": "stationnement-sur-voie-publique-emprises",
    "belib": "belib-points-de-recharge-pour-vehicules-electriques-donnees-statiques",
    "maternelles": "etablissements-scolaires-maternelles",
    "ecoles_elementaires": "etablissements-scolaires-ecoles-elementaires",
    "colleges": "etablissements-scolaires-colleges",
    "espaces_verts": "espaces_verts",
    "que_faire_a_paris": "que-faire-a-paris-",
    "sanisettesparis": "sanisettesparis",
    "marches_decouverts": "marches-decouverts",
    "chantiers_perturbants": "chantiers-perturbants"
}

def main():
    print("=" * 60)
    print("  Downloading Real CSV Datasets from opendata.paris.fr")
    print("=" * 60)
    
    headers = {
        "User-Agent": "UrbanDataExplorer/1.0",
        "Accept-Encoding": "gzip, deflate"
    }
    
    for source_id, dataset_id in DATASET_MAPPING.items():
        # Utiliser limit=1000 pour les datasets volumineux pour des raisons de performance et de taille de stockage
        url = f"https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv?limit=1000"
        dest_path = DOWNLOAD_DIR / f"{source_id}.csv"
        
        print(f"Downloading {source_id} ({dataset_id}) ...")
        
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    raw = response.read()
                    
                    # Decompress if gzipped
                    if response.info().get('Content-Encoding') == 'gzip' or raw.startswith(b'\x1f\x8b'):
                        raw = gzip.decompress(raw)
                        
                    with open(dest_path, "wb") as f:
                        f.write(raw)
                print(f"  [OK] Saved to {dest_path.name} ({len(raw) / 1024:.1f} KB)")
                break
            except Exception as e:
                print(f"  [ERR] Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        else:
            print(f"  [FAIL] Failed to download {source_id}")

if __name__ == "__main__":
    main()
