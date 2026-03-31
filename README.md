# 🏙️ Urban Data Explorer

> Explorer, comprendre et comparer les dynamiques du logement au cœur de Paris.

**Projet réalisé dans le cadre du Mastère Data Engineering et IA DE2**

## 📋 Description

Urban Data Explorer est une plateforme interactive permettant de visualiser et analyser les données urbaines de Paris. Le dashboard propose une navigation fluide par arrondissement, avec cartes interactives, graphiques, timeline historique et comparaison entre quartiers.

L'objectif est de révéler les dynamiques cachées du logement parisien : prix au m², logements sociaux, accessibilité des services, qualité de vie par arrondissement.

## 👥 Équipe Projet
- **[Adam BELOUCIF](https://github.com/Adam-Blf)** - *Data Engineer & Backend*
- **[Emilien MORICE](https://github.com/emilien754)** - *Frontend & Dataviz*
- **Arnaud DISSONGO** - *Data Pipeline & Analytics*

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Sources de Données                    │
│  OpenData Paris · Data.gouv.fr · DVF · GeoJSON          │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │   Pipeline Python    │
              │  Bronze → Silver →   │
              │       Gold           │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   API FastAPI        │
              │  REST + GeoJSON      │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Dashboard Web      │
              │  MapLibre GL JS      │
              │  Chart.js            │
              └─────────────────────┘
```

## 📊 Sources de Données

### OpenData Paris
- Logements sociaux financés à Paris
- Espaces verts et parcs
- Stations Vélib' et disponibilité
- Bornes de recharge électrique Belib'
- Stationnement sur voie publique
- Toilettes publiques (Sanisettes)
- Établissements scolaires (écoles, collèges)
- Marchés découverts
- Événements culturels (Que faire à Paris)
- Aménagements cyclables
- Chantiers perturbants la circulation

### Data.gouv.fr
- Monuments historiques protégés
- Musées de France
- Établissements hospitaliers franciliens
- Transactions immobilières (DVF)

## 🎯 Indicateurs Composites

Quatre indicateurs originaux créés par fusion de données multi-sources :

1. **🌿 Indice de Qualité de Vie** — Espaces verts + services publics + commerces
2. **🚗 Indice de Mobilité Urbaine** — Vélib' + bornes EV + pistes cyclables + stationnement
3. **🏛️ Indice de Patrimoine Culturel** — Monuments + musées + événements
4. **🏘️ Indice de Tension Immobilière** — Logements sociaux + prix/m² + chantiers

## 🚀 Installation

### Prérequis
- Python 3.10+
- Node.js (optionnel, pour serveur de dev)
- Navigateur moderne

### Pipeline de données
```bash
cd pipeline
pip install -r requirements.txt
python run_pipeline.py
```

### API Backend
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
# Ouvrir index.html ou utiliser un serveur local
python -m http.server 3000
```

## 📁 Structure du Projet

```
urban-data-explorer/
├── docs/                    # Documentation technique
│   ├── architecture.md      # Architecture détaillée
│   └── data-catalog.md      # Catalogue des données
├── pipeline/                # Pipeline d'ingestion
│   ├── config.py            # Configuration des sources
│   ├── ingest.py            # Couche Bronze
│   ├── transform.py         # Couche Silver
│   ├── aggregate.py         # Couche Gold
│   └── run_pipeline.py      # Orchestrateur
├── data/                    # Données (Bronze/Silver/Gold)
├── api/                     # API REST FastAPI
│   ├── main.py
│   └── routers/
├── frontend/                # Interface web
│   ├── index.html
│   ├── css/
│   └── js/
└── README.md
```

## 📄 Licence

Projet académique — Mastère Data Engineering et IA DE2
