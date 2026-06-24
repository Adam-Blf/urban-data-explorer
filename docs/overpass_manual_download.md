# Telechargement manuel - sources Overpass 429/504

Sources OSM bloquees par rate-limit lors de l'ingestion automatique.
Placer chaque fichier dans `data/raw/downloads/` avec le nom exact indique.
Etat au 2026-06-24.

## Procedure

1. Ouvrir https://overpass-turbo.eu/
2. Coller la requete dans l'editeur
3. Cliquer **Run**
4. **Export > Data > download as raw data (.csv)** - renommer en `<source_id>.tsv`
5. Placer dans `data/raw/downloads/`

Le separateur est la tabulation `\t`. La premiere ligne doit etre l'en-tete
avec les colonnes exactes de la requete (lat, lon, name, ...).

---

## 1. pompiers.tsv

**Titre** : Casernes de pompiers a Paris - OpenStreetMap
**Fichier cible** : `data/raw/downloads/pompiers.tsv`

```
[out:csv(::lat,::lon,name,amenity,operator;true;"	")][timeout:90];
area["ref:INSEE"="75056"]->.p;
node[amenity=fire_station](area.p);
out body;
```

---

## 2. aires_jeux.tsv

**Titre** : Aires de jeux pour enfants a Paris - OpenStreetMap
**Fichier cible** : `data/raw/downloads/aires_jeux.tsv`
**Note** : remplace l'ancien dataset opendata.paris.fr supprime.

```
[out:csv(::lat,::lon,name,leisure,access,opening_hours;true;"	")][timeout:90];
area["ref:INSEE"="75056"]->.p;
node[leisure=playground](area.p);
out body;
```

---

## 3. stations_velo_osm.tsv

**Titre** : Pistes cyclables et voies vertes (geometrie) - OpenStreetMap
**Fichier cible** : `data/raw/downloads/stations_velo_osm.tsv`

```
[out:csv(::lat,::lon,name,highway,bicycle,surface;true;"	")][timeout:90];
area["ref:INSEE"="75056"]->.p;
node[highway=cycleway](area.p);
out body;
```

---

Une fois les fichiers places, relancer le pipeline :
```
python scripts/run_pipeline.py
```
