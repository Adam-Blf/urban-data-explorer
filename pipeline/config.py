"""
Configuration Globale du Pipeline de Données
Auteurs : Adam BELOUCIF (Adam-Blf), Arnaud DISSONGO (Panason1c)
Rôle : Centralisation des chemins, endpoints API et schémas des datasets.
Dernière mise à jour : 31/03/2026
"""

import os

# --- Gestion des Chemins (Filesystem) ---
# Racine du projet (permet l'exécution depuis n'importe quel dossier)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Architecture Médaille (Medallion Architecture)
BRONZE_DIR = os.path.join(DATA_DIR, "bronze") # Données brutes (Raw)
SILVER_DIR = os.path.join(DATA_DIR, "silver") # Données nettoyées (Cleansed)
GOLD_DIR = os.path.join(DATA_DIR, "gold")     # Données agrégées (Analytics)

# --- Sources de Données (Endpoints) ---

# 1. API OpenData Paris (V2.1)
# Export complet dynamique au format JSON/GeoJSON
PARIS_OPENDATA_BASE = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{dataset}/exports/json"
PARIS_OPENDATA_GEOJSON_BASE = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{dataset}/exports/geojson"

# Catalogue des datasets municipaux
PARIS_DATASETS = {
    "logements_sociaux": {
        "id": "logements-sociaux-finances-a-paris",
        "format": "json"
    },
    "espaces_verts": {
        "id": "espaces_verts",
        "format": "json"
    },
    "velib": {
        "id": "velib-emplacement-des-stations",
        "format": "json"
    },
    "belib": {
        "id": "belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel",
        "format": "json"
    },
    "stationnement_emplacements": {
        "id": "stationnement-voie-publique-emplacements",
        "format": "json"
    },
    "toilettes": {
        "id": "sanisettesparis",
        "format": "json"
    },
    "ecoles": {
        "id": "etablissements-scolaires-ecoles-elementaires",
        "format": "json"
    },
    "colleges": {
        "id": "etablissements-scolaires-colleges",
        "format": "json"
    },
    "marches": {
        "id": "marches-decouverts",
        "format": "json"
    },
    "arbres": {
        "id": "les-arbres",
        "format": "json"
    },
    "commerces": {
        "id": "commerces-a-paris",
        "format": "json"
    },
    "culture_events": {
        "id": "que-faire-a-paris-",
        "format": "json"
    },
    "pistes_cyclables": {
        "id": "amenagements-cyclables",
        "format": "json"
    },
    "chantiers": {
        "id": "chantiers-perturbants",
        "format": "json"
    },
    "arrondissements": { # Fond de carte pour les jointures spatiales
        "id": "arrondissements",
        "format": "geojson"
    },
    "qualite_air": {
        "id": "barometre_aiparif_2021v2",
        "format": "json"
    }
}



# 2. Data.gouv.fr (Plateforme Nationale)
# Téléchargement direct des dernières versions CSV consolidées par le ministère.
DATA_GOUV_DATASETS = {
    "monuments_historiques": {
        # Base Mérimée (Protection du patrimoine)
        "url": "https://www.data.gouv.fr/api/1/datasets/r/3a52af4a-f9da-4dcc-8110-b07774dfb3bc",
        "format": "csv"
    },
    "musees_france": {
        "url": "https://www.data.gouv.fr/api/1/datasets/r/29406189-15e9-4f2f-9e9d-d18649762198",
        "format": "csv"
    }
}
