# Architecture Technique — Urban Data Explorer

## Vue d'ensemble

Le projet suit une architecture **data pipeline classique en 3 couches** (Bronze → Silver → Gold) alimentant une API REST qui sert un dashboard cartographique interactif.

## Couches de données

### 🥉 Bronze — Données Brutes
- Récupération directe depuis les API OpenData Paris et Data.gouv.fr
- Format : JSON et CSV bruts tels que fournis par les API
- Aucune transformation appliquée
- Stockage local dans `data/bronze/`
- Traçabilité : chaque fichier porte le nom du dataset source + timestamp

### 🥈 Silver — Données Nettoyées
- Nettoyage : suppression des doublons, valeurs manquantes
- Normalisation : noms de champs standardisés, types unifiés
- Filtrage géographique : conservation uniquement des données Paris intra-muros
- Géocodage : extraction/normalisation des coordonnées lat/lon
- Enrichissement : ajout du numéro d'arrondissement quand absent
- Stockage : `data/silver/` au format JSON normalisé

### 🥇 Gold — Données Agrégées
- Agrégation par arrondissement
- Calcul des 4 indicateurs composites
- Séries temporelles pour l'évolution historique
- Données prêtes pour la visualisation
- Stockage : `data/gold/` au format JSON

## Stack Technique

| Composant | Technologie | Justification |
|-----------|------------|---------------|
| Pipeline | Python (requests, pandas) | Écosystème data mature |
| API | FastAPI + Uvicorn | Performance async, doc auto |
| Frontend | HTML/CSS/JS vanilla | Légèreté, pas de build |
| Cartographie | MapLibre GL JS | Open-source, performant |
| Graphiques | Chart.js | Simple, responsive |
| Stockage | Fichiers JSON | Pas de BDD nécessaire pour ce volume |

## API REST

### Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/arrondissements` | GeoJSON des limites + indicateurs |
| GET | `/api/logements-sociaux` | Points des logements sociaux |
| GET | `/api/transport` | Vélib', bornes EV, parking |
| GET | `/api/services` | Écoles, toilettes, marchés |
| GET | `/api/culture` | Monuments, musées, événements |
| GET | `/api/indicateurs` | Les 4 indicateurs composites |
| GET | `/api/indicateurs/{id}` | Détail d'un indicateur |
| GET | `/api/compare/{arr1}/{arr2}` | Comparaison entre arrondissements |
| GET | `/api/timeline` | Données d'évolution temporelle |

### Paramètres de filtrage
- `arrondissement` : numéro d'arrondissement (1-20)
- `annee` : année pour les données historiques
- `categorie` : filtre par catégorie de données

## Frontend

### Composants principaux
1. **Carte choroplèthe** — Coloration des arrondissements selon l'indicateur sélectionné
2. **Couches de points** — Vélib', bornes, écoles, etc. avec popups détaillés
3. **Panneau latéral** — Graphiques et statistiques de l'arrondissement sélectionné
4. **Timeline** — Curseur temporel pour visualiser l'évolution
5. **Mode comparaison** — Juxtaposition de 2 arrondissements
6. **Sélecteur de couches** — Activation/désactivation des couches de données

## Diagramme de flux

```
Utilisateur → Frontend (MapLibre)
                  ↓ fetch()
             API FastAPI
                  ↓ lecture
            data/gold/*.json
```
