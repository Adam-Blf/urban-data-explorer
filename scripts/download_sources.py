"""Téléchargement du GeoJSON IRIS de Paris et génération de données locales CSV.

Assure que le pipeline ETL Polars peut s'exécuter hors-ligne immédiatement
avec des données parisiennes réalistes.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = ROOT / "data" / "raw" / "downloads"

# URL GeoJSON officiel des IRIS de Paris (Île-de-France Open Data / INSEE)
IRIS_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson"


def generate_mock_csv(path: Path, columns: list[str], row_generator, count: int = 150):
    """Génère un fichier CSV réaliste avec le séparateur point-virgule (standard Paris)."""
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(";".join(columns) + "\n")
        for _ in range(count):
            row = row_generator()
            # Échapper les points-virgules
            row_str = [str(x).replace(";", ",") if x is not None else "" for x in row]
            f.write(";".join(row_str) + "\n")


def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print("Initialisation du repertoire de telechargement...")

    # 1. Télécharger le GeoJSON des arrondissements / IRIS de Paris
    iris_path = DOWNLOAD_DIR / "paris_iris.geojson"
    if not iris_path.exists():
        print("  -> Telechargement de paris_iris.geojson...")
        try:
            r = requests.get(IRIS_URL, timeout=15)
            if r.status_code == 200:
                with open(iris_path, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f)
                print("  -> GeoJSON telecharge avec succes.")
            else:
                raise Exception(f"Code {r.status_code}")
        except Exception as e:
            print(f"  -> Echec du telechargement ({e}). Creation d'un GeoJSON de secours...")
            # Créer un GeoJSON minimal avec 20 arrondissements
            features = []
            for i in range(1, 21):
                code = f"750{i:02d}"
                features.append({
                    "type": "Feature",
                    "properties": {
                        "code_iris": f"{code}0101",
                        "nom_iris": f"IRIS Paris {i}e",
                        "insee_com": code
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [2.35 + 0.01 * i, 48.85 + 0.005 * i],
                            [2.36 + 0.01 * i, 48.85 + 0.005 * i],
                            [2.36 + 0.01 * i, 48.86 + 0.005 * i],
                            [2.35 + 0.01 * i, 48.86 + 0.005 * i],
                            [2.35 + 0.01 * i, 48.85 + 0.005 * i]
                        ]]
                    }
                })
            geojson = {"type": "FeatureCollection", "features": features}
            with open(iris_path, "w", encoding="utf-8") as f:
                json.dump(geojson, f)

    # 2. Générer des CSV parisiens cohérents
    print("  -> Generation des jeux de donnees d'entrainement (CSV)...")

    # Logements Sociaux
    generate_mock_csv(
        DOWNLOAD_DIR / "logements_sociaux.csv",
        ["Arrondissement", "Adresse du programme", "geo_point_2d", "Nombre de logements"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{random.randint(1, 150)} Rue de Paris",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}",
            random.randint(5, 80)
        ]
    )

    # Vélib Stations
    generate_mock_csv(
        DOWNLOAD_DIR / "velib_stations.csv",
        ["Nom de la station", "Coordonnées géographiques", "Capacité"],
        lambda: [
            f"Station Velib {random.randint(1000, 9999)}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}",
            random.choice([20, 30, 45, 60])
        ]
    )

    # Vélib Disponibilité
    generate_mock_csv(
        DOWNLOAD_DIR / "velib_disponibilite.csv",
        ["Code INSEE communes équipées", "Coordonnées géographiques", "Vélos disponibles"],
        lambda: [
            f"751{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}",
            random.randint(0, 25)
        ]
    )

    # Bornes Belib
    generate_mock_csv(
        DOWNLOAD_DIR / "belib.csv",
        ["arrondissement", "coordonneesXY", "adresse_station", "nombre_points_recharge"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}",
            f"{random.randint(1, 100)} Boulevard Saint-Germain",
            random.choice([2, 4, 6])
        ]
    )

    # Écoles Maternelles
    generate_mock_csv(
        DOWNLOAD_DIR / "maternelles.csv",
        ["Arrondissement", "Adresse", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{random.randint(1, 100)} Rue de L'Ecole",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Écoles Élémentaires
    generate_mock_csv(
        DOWNLOAD_DIR / "ecoles_elementaires.csv",
        ["Arrondissement", "Adresse", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{random.randint(1, 100)} Rue du Tableau",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Collèges
    generate_mock_csv(
        DOWNLOAD_DIR / "colleges.csv",
        ["Arrondissement", "Adresse", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{random.randint(1, 100)} Rue du College",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Espaces Verts
    generate_mock_csv(
        DOWNLOAD_DIR / "espaces_verts.csv",
        ["Code postal", "Geo point", "Nom de l'espace vert"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}",
            f"Square {random.choice(['Monceau', 'des Batignolles', 'du Temple', 'Louvois'])}"
        ]
    )

    # Que faire à Paris (Culture)
    generate_mock_csv(
        DOWNLOAD_DIR / "que_faire_a_paris.csv",
        ["Code postal", "Coordonnées géographiques", "Adresse du lieu", "Titre"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}",
            f"{random.randint(1, 100)} Rue de Rivoli",
            "Exposition d'Art Moderne"
        ]
    )

    # Sanisettes (Toilettes)
    generate_mock_csv(
        DOWNLOAD_DIR / "sanisettesparis.csv",
        ["ARRONDISSEMENT", "ADRESSE", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{random.randint(1, 100)} Rue de l'Hygiene",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Marchés découverts
    generate_mock_csv(
        DOWNLOAD_DIR / "marches_decouverts.csv",
        ["Arrondissement", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Chantiers perturbants
    generate_mock_csv(
        DOWNLOAD_DIR / "chantiers_perturbants.csv",
        ["Code postal de l'arrondissement", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Aménagements cyclables
    generate_mock_csv(
        DOWNLOAD_DIR / "amenagements_cyclables.csv",
        ["Arrondissement", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Stationnement Emplacements
    generate_mock_csv(
        DOWNLOAD_DIR / "stationnement_voie_publique_emplacements.csv",
        ["Arrondissement", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    # Stationnement Emprises
    generate_mock_csv(
        DOWNLOAD_DIR / "stationnement_voie_publique_emprises.csv",
        ["Arrondissement", "geo_point_2d"],
        lambda: [
            f"750{random.randint(1, 20):02d}",
            f"{48.85 + random.uniform(-0.04, 0.04)},{2.35 + random.uniform(-0.06, 0.06)}"
        ]
    )

    print("  -> Tous les CSV requis ont ete crees localement.")


if __name__ == "__main__":
    main()
