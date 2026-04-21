# 🏙️ Urban Data Explorer: Guide Complet du Projet (A-Z)

Bienvenue dans le guide technique de **Urban Data Explorer**, la plateforme d'intelligence spatiale pour l'analyse des arrondissements de Paris. Ce document explique la conception, l'architecture et le fonctionnement du projet de bout en bout.

---

## 🏛️ PARTIE A : Vision & Objectifs

L'objectif de ce projet est de fournir un tableau de bord interactif permettant de comparer les arrondissements de Paris selon des critères objectifs issus de la donnée publique (**Open Data**).

Le projet se concentre sur **4 dimensions clés** :
1.  **🌿 Qualité de Vie** : Espaces verts, arbres, écoles.
2.  **🚗 Mobilité** : Réseau Vélib', bornes électriques, pistes cyclables.
3.  **🏛️ Patrimoine & Culture** : Monuments historiques, musées, événements culturels.
4.  **🏘️ Tension Immobilière** : Prix au m², logements sociaux.

---

## 🏗️ PARTIE B : Architecture des Données (Medallion)

Nous utilisons une architecture de type **Medallion**, standard de l'industrie pour les pipelines de données modernes.

### 1. Couche BRONZE (Raw)
- **Rôle** : Extraction des données brutes depuis les API sources.
- **Sources** : OpenData Paris, Data.gouv.fr.
- **Format** : JSON, CSV ou GeoJSON tels quels.
- **Code** : `pipeline/ingest.py`.

### 2. Couche SILVER (Cleansed)
- **Rôle** : Nettoyage, standardisation et **jointures spatiales**.
- **Opérations** : Conversion des types, split des coordonnées (lat/lon), assignation de l'arrondissement via jointure Point-in-Polygon.
- **Code** : `pipeline/transform.py`.

### 3. Couche GOLD (Analytics)
- **Rôle** : Agrégation et scoring.
- **Opérations** : Calcul des indices composites par arrondissement (ex: score 1-100), génération d'un GeoJSON consolidé pour la carte.
- **Code** : `pipeline/aggregate.py`.

---

## 💻 PARTIE C : Stack Technique & Backend

### Backend (Python/FastAPI)
- **FastAPI** : Framework asynchrone ultra-performant pour exposer les données.
- **GeoPandas & Shapely** : Outils de manipulation géospatiale pour le pipeline.
- **Httpx** : Utilisé pour les tâches de fond (Keep-Alive) sur Render.

### Frontend (Modern Web)
- **MapLibre GL JS** : Moteur de rendu cartographique pour visualiser les couches de données.
- **Chart.js** : Visualisation des KPIs et radars de comparaison.
- **Glassmorphism UI** : Design moderne basé sur la transparence et le flou (CSS Vanilla).

---

## ☁️ PARTIE D : Déploiement & DevOps

### Hébergement
- **API** : Déployée sur **Render**. Une tâche de fond effectue un ping toutes les 14 minutes pour éviter la mise en veille du plan "Free".
- **Frontend** : Déployé sur **Vercel** pour une performance statique optimale.

### CI/CD
Le déploiement est automatisé via GitHub. Chaque push sur la branche `main` déclenche le build sur Render et Vercel.

---

## 📂 PARTIE E : Structure du Code

```bash
urban-data-explorer/
├── api/              # Serveur FastAPI
├── data/             # Stockage Bronze/Silver/Gold
├── pipeline/         # Scripts ETL (Ingest -> Aggregate)
├── frontend/         # Code HTML/CSS/JS du dashboard
└── render.yaml       # Configuration du Blueprint Render
```

---

## 🚀 PARTIE F : Comment ça marche ?

1.  **Ingestion** : Les scripts récupèrent 15+ datasets différents (écoles, bornes de recharge, arbres remarquables...).
2.  **Transformation** : Le pipeline vérifie la position GPS de chaque donnée pour savoir dans quel arrondissement elle se trouve.
3.  **Visualisation** : L'API renvoie ces statistiques au Frontend qui affiche une carte thermique et des graphiques.
4.  **Comparaison** : L'utilisateur peut sélectionner deux arrondissements pour voir lequel performe le mieux sur quel indice.

---

**Ceci est un projet Data Engineering complet, prêt pour la mise en production.**
