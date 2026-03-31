# Catalogue de Données — Urban Data Explorer

## Sources de données

Ce document recense l'ensemble des sources de données utilisées dans le projet, leur provenance, leur format, et la justification de leur sélection.

---

## 1. OpenData Paris (`opendata.paris.fr`)

### 1.1 Logements sociaux financés à Paris
- **Dataset** : `logements-sociaux-finances-a-paris`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/logements-sociaux-finances-a-paris/exports/json`
- **Format** : JSON (points géolocalisés)
- **Champs clés** : adresse, arrondissement, année, nb_logements, catégorie de financement (PLAI, PLUS, PLS), mode de réalisation
- **Pertinence** : Indicateur direct de la politique de logement social par arrondissement et par année
- **Qualité** : ✅ Géolocalisé, séries temporelles depuis 2001

### 1.2 Espaces verts
- **Dataset** : `espaces_verts`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/espaces_verts/exports/json`
- **Format** : JSON (polygones MultiPolygon)
- **Champs clés** : nom, type, catégorie, surface_totale, code postal
- **Pertinence** : Composante majeure de l'indice de qualité de vie
- **Qualité** : ✅ Données surfaciques précises

### 1.3 Stations Vélib'
- **Dataset** : `velib-emplacement-des-stations`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-emplacement-des-stations/exports/json`
- **Format** : JSON (points)
- **Champs clés** : stationcode, name, capacity, coordonnees_geo
- **Pertinence** : Composante de l'indice de mobilité urbaine
- **Qualité** : ✅ ~1400 stations, données fiables

### 1.4 Bornes de recharge Belib'
- **Dataset** : `belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel/exports/json`
- **Format** : JSON (points)
- **Champs clés** : id_pdc, statut, adresse, arrondissement, coordonnees
- **Pertinence** : Infrastructure de mobilité électrique
- **Qualité** : ✅ Données temps réel

### 1.5 Stationnement sur voie publique (emplacements)
- **Dataset** : `stationnement-voie-publique-emplacements`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/stationnement-voie-publique-emplacements/exports/json`
- **Format** : JSON (points)
- **Champs clés** : type, régime, arrondissement, localisation
- **Pertinence** : Composante stationnement de l'indice de mobilité
- **Qualité** : ⚠️ Données évolutives, non exhaustives

### 1.6 Toilettes publiques (Sanisettes)
- **Dataset** : `sanisettesparis`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/sanisettesparis/exports/json`
- **Format** : JSON (points)
- **Champs clés** : type, arrondissement, horaire, accès PMR, coordonnées
- **Pertinence** : Service public de proximité, indicateur d'accessibilité
- **Qualité** : ✅ Données à jour

### 1.7 Écoles élémentaires
- **Dataset** : `etablissements-scolaires-ecoles-elementaires`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/etablissements-scolaires-ecoles-elementaires/exports/json`
- **Format** : JSON (points)
- **Champs clés** : nom, arrondissement, type, coordonnées
- **Pertinence** : Service public essentiel, composante qualité de vie
- **Qualité** : ✅ Données officielles

### 1.8 Collèges
- **Dataset** : `etablissements-scolaires-colleges`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/etablissements-scolaires-colleges/exports/json`
- **Format** : JSON (points)
- **Pertinence** : Complément des écoles pour l'offre éducative
- **Qualité** : ✅ Données officielles

### 1.9 Marchés découverts
- **Dataset** : `marches-decouverts`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/marches-decouverts/exports/json`
- **Format** : JSON (points)
- **Champs clés** : nom, produits, arrondissement, jours, horaires
- **Pertinence** : Commerce de proximité, animation du quartier
- **Qualité** : ✅ Géolocalisé

### 1.10 Que faire à Paris (Culture)
- **Dataset** : `que-faire-a-paris-`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/exports/json`
- **Format** : JSON (points)
- **Champs clés** : titre, catégorie, date, lieu, prix, accessibilité
- **Pertinence** : Offre culturelle, composante patrimoine
- **Qualité** : ✅ Données riches

### 1.11 Aménagements cyclables
- **Dataset** : `amenagements-cyclables`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/amenagements-cyclables/exports/json`
- **Format** : JSON (lignes)
- **Champs clés** : type d'aménagement, arrondissement, longueur
- **Pertinence** : Infrastructure vélo, composante mobilité
- **Qualité** : ✅ Données issues d'OSM

### 1.12 Chantiers perturbants
- **Dataset** : `chantiers-perturbants`
- **API** : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/chantiers-perturbants/exports/json`
- **Format** : JSON (polygones)
- **Champs clés** : maître d'ouvrage, objet, impact circulation, statut
- **Pertinence** : Impact urbain, composante tension immobilière
- **Qualité** : ⚠️ Non exhaustif

---

## 2. Data.gouv.fr

### 2.1 Monuments historiques
- **Dataset** : `immeubles-proteges-au-titre-des-monuments-historiques-2`
- **Ressource** : CSV (~100 Mo) avec coordonnées WGS84
- **Champs clés** : référence, dénomination, adresse, commune, siècle, type de protection, coordonnées
- **Pertinence** : Patrimoine bâti, composante indice culturel
- **Qualité** : ✅ Données officielles Ministère de la Culture

### 2.2 Musées de France
- **Dataset** : `liste-des-musees-de-france`
- **Ressource** : CSV (~280 Ko) avec géolocalisation
- **Champs clés** : nom, adresse, commune, département, coordonnées
- **Pertinence** : Offre muséale, composante indice culturel
- **Qualité** : ✅ Liste officielle, mise à jour annuelle

---

## 3. Données de référence

### 3.1 Limites des arrondissements de Paris
- **Source** : GeoJSON OpenDataSoft / data.gouv.fr
- **Format** : GeoJSON (polygones)
- **Pertinence** : Fond de carte choroplèthe
- **Qualité** : ✅ Données géographiques de référence

### 3.2 Prix au m² par arrondissement
- **Source** : Agrégation de données DVF (Demandes de Valeurs Foncières) et données notariales
- **Format** : JSON agrégé par arrondissement et par année
- **Pertinence** : Indicateur central du marché immobilier
- **Qualité** : ✅ Données basées sur les transactions réelles

---

## Contraintes et limites

| Contrainte | Impact | Mitigation |
|-----------|--------|------------|
| Volume de données espaces verts (géométries lourdes) | Temps de chargement | Simplification des polygones au Silver |
| Données non exhaustives (stationnement, chantiers) | Couverture partielle | Mention dans la documentation |
| Monuments historiques (~100 Mo CSV) | Filtrage nécessaire | Filtre sur département 75 au Bronze |
| Données temps réel (Belib') | Obsolescence rapide | Snapshot à la date du pipeline |
