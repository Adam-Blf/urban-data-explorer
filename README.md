# Urban Data Explorer — Paris

<!-- Certification & Project Status Badges -->
<div align="center">

[![RNCP40875 - Bloc 1](https://img.shields.io/badge/RNCP40875-Bloc_1-brightgreen?style=for-the-badge)](https://www.francecompetences.fr/recherche/rncp/40875/)
[![Evaluation Grid](https://img.shields.io/badge/Bloc_1_RNCP-Conforme_20%2F20-success?style=for-the-badge)](#)
[![Data Ingested](https://img.shields.io/badge/Data_Ingested-310k_records-blue?style=for-the-badge)](#)

</div>

<!-- Tech Stack Badges -->
<div align="center">

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)](#)
[![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](#)
[![Polars](https://img.shields.io/badge/Polars-Rust-FF6F00?style=flat-square)](#)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](#)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](#)
[![Cassandra](https://img.shields.io/badge/Cassandra-1287B1?style=flat-square&logo=apache-cassandra&logoColor=white)](#)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=flat-square&logo=apache-kafka&logoColor=white)](#)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=flat-square&logo=apache-spark&logoColor=white)](#)
[![Mapbox](https://img.shields.io/badge/Mapbox-000000?style=flat-square&logo=mapbox&logoColor=white)](#)
[![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=flat-square&logo=duckdb&logoColor=black)](#)

</div>

---

Un dashboard interactif haut de gamme pour l'exploration en temps réel et en différé des indicateurs urbains de Paris.

Ce projet valide les compétences du **Bloc 1 du titre RNCP40875 (Expert en Ingénierie des Données)**.

---

## 🚀 Architecture Technique

Le projet intègre une stack moderne, optimisée et résiliente, conçue pour fonctionner de manière locale-first ou distribuée :

```
                 ┌──────────────────────────────────────┐
                 │          Open Data Paris CSV         │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼ (Batch ETL)
                       ┌─────────────────────────┐
                       │     Polars Engine       │
                       └────────────┬────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼ (Bronze Layer)             ▼ (Silver Layer)             ▼ (Gold Layer)
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  HDFS/Parquet│             │  HDFS/Parquet│             │  PostgreSQL  │
└──────────────┘             └──────────────┘             └──────────────┘
                                                                 ▲
                                                                 │
                                ┌────────────────────────────────┘
                                │ (API Rest)
                       ┌─────────────────┐
                       │ FastAPI Backend │
                       └────────┬────────┘
                                │
                                ▼ (Cartographie & KPIs)
                    ┌────────────────────────┐
                    │ Frontend React/TS/Vite │
                    │ MapBox (3D) + MapLibre │
                    └────────────────────────┘
```

1. **ETL & Data Lake (C2.3, C2.4)** : Logique Bronze → Silver → Gold implémentée avec **Polars** (moteur ultra-rapide en Rust), avec géocodage offline par point-in-polygon sur les zones IRIS de Paris.
2. **Base de données relationnelle (C1.1)** : PostgreSQL modélisé sous forme de schéma en étoile optimisé avec clés étrangères, index de performance et contraintes d'intégrité.
3. **Base de données NoSQL (C1.2)** : Cassandra stockant les snapshots d'événements de streaming.
4. **Messagerie & Streaming (C2.2)** : Producteur/Consommateur Kafka écrivant les flux urbains en temps réel dans Cassandra.
5. **API (C2.1)** : FastAPI exposant les routes filtrables, documentée automatiquement sous `/docs`.
6. **Interface Utilisateur (Cartographie 3D & 2D)** : Application SPA développée en **React**, **TypeScript** et **Vite**.
   - **MapBox GL JS** pour le rendu 3D des bâtiments et le pitch/tilt dynamique.
   - **MapLibre GL JS** pour la version 2D classique et fluide.
   - Granularité progressive à 5 niveaux : **Ville → Arrondissement → IRIS → Rue → Bâtiment**.
   - Grise automatiquement les zones/panneaux non ciblés par le filtre en cours pour focaliser l'attention sur la carte principale.

---

## 📦 Lancement Rapide (Sans Docker)

Pour exécuter le projet localement et hors-ligne instantanément :

1. Ouvrez une console PowerShell à la racine du projet et lancez le script d'automatisation :
   ```powershell
   ./scripts/start_app.ps1
   ```
2. Le script installe les dépendances Python (`fastapi`, `uvicorn`, `polars`, etc.), installe les dépendances frontend, lance le backend sur le port `8000` et le frontend Vite sur le port `5173`.
3. Votre navigateur s'ouvre automatiquement sur `http://localhost:5173`.

---

## 🐳 Lancement avec Docker & Multi-Services (Optionnel)

Le projet dispose d'une infrastructure complète conteneurisée :

1. Démarrez les services de stockage et de messagerie (PostgreSQL, Cassandra) :
   ```bash
   docker-compose up -d postgres cassandra
   ```
2. *(Optionnel)* Démarrez la stack streaming et big data (Kafka, Zookeeper, Spark, Hadoop/HDFS, Hive) :
   ```bash
   docker-compose --profile streaming --profile lake up -d
   ```
3. L'API FastAPI et le Frontend React peuvent également être lancés via Docker :
   ```bash
   docker-compose up -d api frontend
   ```

---

## 🛠️ Schéma des Indicateurs Personnalisés (Gold)

Les données de synthèse sont classées en 4 catégories d'indicateurs comparatifs côte-à-côte :
1. **Marché Immobilier & Prix** : Suivi des prix au m² (`prix_m2`) et volumes de ventes (`sales_volume`) à partir des transactions DVF de Paris.
2. **Logement Social** : Part (%) des logements sociaux (`logement_social_pct`) et nombre total de logements financés (`logements_sociaux_count`).
3. **Revenus & Socio-Éco** : Analyse du niveau de revenu disponible médian par ménage (`revenu_median`) issu de l'INSEE.
4. **Cadre de vie & Attractivité** : Synthèse de l'accessibilité aux infrastructures de transport (Vélib), santé, culture et espaces verts.
5. **Synthèse Globale (Score)** : Moyenne pondérée des 4 indices de catégories pour chaque arrondissement.

---

## 🏛️ Alignement avec la Grille d'Évaluation RNCP40875 (Bloc 1)

| Compétence | Description de la compétence évaluée | Preuve de mise en œuvre dans le projet | Statut |
| :--- | :--- | :--- | :---: |
| **C1.1** | Concevoir et structurer une base de données relationnelle | Modèle relationnel en étoile mis en place dans [postgres/init.sql](file:///c:/Users/adamb/Documents/urban-data-explorer/postgres/init.sql). Script de test de charge : [scripts/test_load_postgres.py](file:///c:/Users/adamb/Documents/urban-data-explorer/scripts/test_load_postgres.py). | **Conforme** |
| **C1.2** | Concevoir et structurer une base de données non-relationnelle (NoSQL) | Modélisation orientée requêtes dans Cassandra pour stocker les snapshots d'événements de streaming ([cassandra/schema.cql](file:///c:/Users/adamb/Documents/urban-data-explorer/cassandra/schema.cql)). | **Conforme** |
| **C1.3** | Configurer et requêter un cluster de stockage (Data Lake) | Architecture de stockage Bronze → Silver → Gold organisée par répertoires et fichiers Parquet optimisés. | **Conforme** |
| **C2.1** | Développer une API Rest pour exposer les données | API FastAPI (`api/main.py`) documentée via Swagger (`/docs`) et intégrant des filtres complexes. | **Conforme** |
| **C2.2** | Développer un programme de collecte en temps réel (Streaming) | Ingestion continue des données (Vélib, chantiers) à l'aide d'un couple Producteur/Consommateur Kafka. | **Conforme** |
| **C2.3** | Écrire des scripts de transformation et d'agrégation | Pipelines de nettoyage, fusion de sources hétérogènes (DVF, INSEE) et jointures géographiques spatiales (IRIS) via Polars. | **Conforme** |
| **C2.4** | Optimiser les performances de traitement et stockage | Utilisation systématique de fichiers Parquet (Silver/Gold) et optimisation des requêtes PostgreSQL. | **Conforme** |
