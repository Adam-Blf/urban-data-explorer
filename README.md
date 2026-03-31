# 🏙️ Urban Data Explorer

> **Le futur du logement parisien, décrypté par la donnée.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![MapLibre](https://img.shields.io/badge/MapLibre-GL_JS-ff6600?style=for-the-badge&logo=maplibre&logoColor=white)](https://maplibre.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Medallion-DA70D6?style=for-the-badge&logo=google-cloud&logoColor=white)](#-architecture-technique)
[![Quality](https://img.shields.io/badge/Data_Quality-Audit_Passed-success?style=for-the-badge&logo=checkmarx&logoColor=white)]()
[![Documentation](https://img.shields.io/badge/Documentation-Complete-informational?style=for-the-badge&logo=read-the-docs&logoColor=white)](./docs/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](./LICENSE)

---

**Urban Data Explorer** est une plateforme d'intelligence spatiale conçue pour analyser les dynamiques socio-économiques et immobilières de Paris. Ce projet suit une architecture **Medallion (Bronze/Silver/Gold)** pour transformer des données brutes hétérogènes en indicateurs décisionnels haut de gamme.

## 👥 Équipe Projet & Rôles

Ce projet a été réalisé dans le cadre du **Mastère Data Engineering et IA (DE2)** par :

| Membre | Rôle Principal | Responsabilités Techniques |
| :--- | :--- | :--- |
| **[Adam BELOUCIF](https://github.com/Adam-Blf)** | **Architecte Lead & Backend** | Design système, API REST FastAPI, Déploiement |
| **[Emilien MORICE](https://github.com/emilien754)** | **Dataviz & Silver Pipeline** | Frontend MapLibre, Transformation spatiale |
| **[Arnaud DISSONGO (Panason1c)](https://github.com/Panason1c)** | **Data Engineer & Analytics** | Ingestion (Bronze), Agrégation (Gold) |

---

## 🏗️ Architecture Technique (Architecture Médaille)

Nous avons implémenté un pipeline de données industriel divisé en trois couches logiques :

```mermaid
graph TD
    subgraph "Sources Externes"
        OP[OpenData Paris]
        DG[Data.gouv.fr]
        DVF[Base DVF]
    end

    subgraph "Pipeline de Données (Python/Pandas/GeoPandas)"
        B[<b>Bronze Layer</b><br/>Données Brutes / JSON/CSV]
        S[<b>Silver Layer</b><br/>Nettoyage / Spatial Join / Normalisation]
        G[<b>Gold Layer</b><br/>Calcul des Indices / Agrégation par Arrondissement]
    end

    subgraph "Service & Visualisation"
        API[FastAPI Backend]
        WEB[Dashboard Interactif<br/>MapLibre GL JS / Chart.js]
    end

    OP --> B
    DG --> B
    DVF --> B
    B --> S
    S --> G
    G --> API
    API --> WEB
```

---

## 📊 Stratégie de Données (15+ Datasets)

Le projet fusionne des sources gouvernementales et municipales pour créer 4 indicateurs composites :

1.  **🌿 Indice de Qualité de Vie** : Densité d'espaces verts et proximité des services publics (écoles, collèges, hospitalier).
2.  **🚗 Indice de Mobilité Urbaine** : Connectivité Vélib', bornes de recharge électrique, pistes cyclables et fluidité du stationnement.
3.  **🏛️ Indice de Patrimoine Culturel** : Concentration en monuments historiques, musées nationaux et richesse de l'agenda culturel.
4.  **🏘️ Indice de Tension Immobilière** : Ratio de logements sociaux par rapport au prix moyen au m² et impact des chantiers urbains.

---

## 🧩 Structure du Projet

```bash
urban-data-explorer/
├── api/                  # Backend : FastAPI (Adam BELOUCIF)
├── data/                 # Entrepôt local (Bronze/Silver/Gold)
├── docs/                 # Documentation technique approfondie
├── frontend/             # Dashboard interactif (Emilien MORICE)
└── pipeline/             # ETL & Logic de calcul (Arnaud & Emilien)
    ├── ingest.py         # Ingestion (Phase Bronze)
    ├── transform.py      # Nettoyage Spatial (Phase Silver)
    ├── aggregate.py      # Analytics (Phase Gold)
    └── data_quality.py   # Tests de qualité (Phase Audit)
```

---

## 🚀 Lancement Rapide

### 1. Préparation de la donnée (ETL)
```bash
cd pipeline
pip install -r requirements.txt
python run_pipeline.py
```

### 2. Démarrage de l'API
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Consultation du Dashboard
Ouvrez le fichier `frontend/index.html` dans un navigateur ou lancez :
```bash
cd frontend
python -m http.server 3000
```

