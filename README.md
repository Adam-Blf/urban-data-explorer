# Urban Data Explorer

![Status](https://img.shields.io/badge/status-academic-blue)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?logo=duckdb&logoColor=black)
![MapLibre](https://img.shields.io/badge/MapLibre-396CB2?logo=maplibre&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![EFREI M1](https://img.shields.io/badge/EFREI-M1_Data_Eng-000091)

Explorer, comprendre et comparer les dynamiques du logement au cœur de Paris.

Plateforme complète : pipeline data (Bronze/Silver/Gold) → API FastAPI → dashboard cartographique MapLibre.

## Architecture

```
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │  Sources API │──▶│   Bronze     │──▶│   Silver     │──▶│    Gold      │
 │  (opendata)  │   │  (raw json)  │   │  (cleaned)   │   │ (aggregated) │
 └──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘
                                                                 │
                                                          ┌──────▼───────┐
                                                          │  FastAPI     │
                                                          └──────┬───────┘
                                                                 │
                                                          ┌──────▼───────┐
                                                          │  MapLibre UI │
                                                          └──────────────┘
```

Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) et [docs/DATA_CATALOG.md](docs/DATA_CATALOG.md).

## Sources de données

- **Arrondissements de Paris** (GeoJSON) · [opendata.paris.fr](https://opendata.paris.fr/explore/dataset/arrondissements/)
- **Logements sociaux par arrondissement** · opendata.paris.fr
- **DVF · Demandes de valeurs foncières** · [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/)
- **Qualité de l'air** (indicateur composite) · Airparif / opendata.paris.fr
- **Délits enregistrés** · data.gouv.fr

4 niveaux d'information cartographiés + 4 indicateurs composites (cf. `pipeline/gold/indicators.py`).

## Quick start

```bash
# Pipeline
pip install -r pipeline/requirements.txt
python -m pipeline.run

# API
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && python -m http.server 5173
# http://localhost:5173
```

Ou avec Docker :

```bash
docker compose up
```

## Stack

- **Data** · Python, pandas, geopandas, requests, DuckDB
- **API** · FastAPI, uvicorn
- **Front** · MapLibre GL JS, Chart.js, vanilla JS
- **Infra** · Docker Compose, GitHub Actions (pipeline planifié)

## Contributeurs

- [@Adam-Blf](https://github.com/Adam-Blf)
- [@Panason1c](https://github.com/Panason1c)
- [@emilien754](https://github.com/emilien754)


---

<p align="center">
  <sub>Par <a href="https://adam.beloucif.com">Adam Beloucif</a> · Data Engineer & Fullstack Developer · <a href="https://github.com/Adam-Blf">GitHub</a> · <a href="https://www.linkedin.com/in/adambeloucif/">LinkedIn</a></sub>
</p>
