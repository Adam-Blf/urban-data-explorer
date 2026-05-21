# Urban Data Explorer — Paris

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

## 🛠️ Schéma des Indicateurs Personnalisés (Gold)

Nous fusionnons les 19 sources thématiques en 4 scores synthétiques :
1. **Accessibilité** : Équilibre entre parcs, stations Vélib/bornes de recharge, écoles et sanitaires, pénalisé par les chantiers.
2. **Pression Urbaine** : Mesure de la densité de chantiers en cours et des emplacements de stationnement.
3. **Attractivité** : Pondération des espaces verts, événements culturels et volume de logements sociaux financés.
4. **Qualité de vie (Score Global)** : Combinaison pondérée des trois indices précédents.
