"""
Phase Silver : Nettoyage et Normalisation Spatiale
Auteur : Emilien MORICE (emilien754)
Rôle : Transformation des données brutes en données propres. Attribution des arrondissements via Spatial Join.
"""

import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from config import BASE_DIR, BRONZE_DIR, SILVER_DIR, PARIS_DATASETS, DATA_GOUV_DATASETS

def ensure_silver_dir():
    """Crée le répertoire data/silver si nécessaire."""
    if not os.path.exists(SILVER_DIR):
        os.makedirs(SILVER_DIR)
        print(f"Creating Silver directory: {SILVER_DIR}")

def load_arrondissements():
    """
    Charge le fond de carte des arrondissements (GeoJSON) pour les jointures spatiales.
    
    Returns:
        GeoDataFrame: Les polygones des arrondissements avec leur numéro.
    """
    path = os.path.join(BRONZE_DIR, "arrondissements.geojson")
    if not os.path.exists(path):
        print("ERROR: arrondissements.geojson not found in Bronze layer!")
        return None
        
    try:
        # Tentative de lecture standard
        gdf = gpd.read_file(path)
    except Exception as e:
        # Fallback pour les erreurs d'attribut Fiona (AttributeError: module 'fiona' has no attribute 'path')
        print(f"Warning: Standard gpd.read_file failed ({e}). Attempting JSON fallback...")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Gestion des GeoJSON FeatureCollection
        if 'features' in data:
             gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
        else:
             print("ERROR: GeoJSON does not contain features.")
             return None
    
    # Normalisation du numéro d'arrondissement (c_ar ou c_arint selon l'API)
    if 'c_ar' in gdf.columns:
        gdf['arrondissement'] = gdf['c_ar'].astype(int)
    elif 'c_arint' in gdf.columns:
        gdf['arrondissement'] = gdf['c_arint'].astype(int)
    
    return gdf[['arrondissement', 'geometry']]

def assign_arrondissement(df, lat_col, lon_col, arrondissements_gdf):
    """
    Réalise une jointure spatiale (Point-in-Polygon) pour assigner un arrondissement à chaque coordonnée.
    """
    if 'arrondissement' not in df.columns:
        df['arrondissement'] = 0

    if arrondissements_gdf is None or df.empty or lat_col not in df.columns or lon_col not in df.columns:
        return df
    
    # Nettoyage des lignes sans coordonnées
    df_coords = df.dropna(subset=[lat_col, lon_col]).copy()
    if df_coords.empty:
        return df
    
    # Génération de la géométrie vectorielle
    geometry = [Point(xy) for xy in zip(df_coords[lon_col], df_coords[lat_col])]
    gdf_points = gpd.GeoDataFrame(df_coords, geometry=geometry, crs="EPSG:4326")
    
    # Suppression de la colonne arrondissement existante pour éviter les collisions (arrondissement_left/right)
    if 'arrondissement' in gdf_points.columns:
        gdf_points = gdf_points.drop(columns=['arrondissement'])
    
    # Jointure spatiale
    joined = gpd.sjoin(gdf_points, arrondissements_gdf, how="left", predicate="within")
    
    # Application des résultats
    if 'arrondissement' in joined.columns:
        df.loc[df_coords.index, 'arrondissement'] = joined['arrondissement'].fillna(0).astype(int).values
        
    df['arrondissement'] = df['arrondissement'].fillna(0).astype(int)
    return df


def clean_and_save(data, name):
    """Sauvegarde les données nettoyées au format JSON."""
    target_path = os.path.join(SILVER_DIR, f"{name}.json")
    with open(target_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Success: {target_path} ({(len(data))} records)")

def transform_logements_sociaux():
    """Nettoyage spécifique des données de logements sociaux."""
    path = os.path.join(BRONZE_DIR, "logements_sociaux.json")
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    cleaned = []
    for item in raw:
        if not item.get("geo_point_2d"): continue
        cleaned.append({
            "adresse": item.get("adresse_programme"),
            "arrondissement": int(item.get("arrdt", 0)),
            "annee": int(item.get("annee", 0)) if item.get("annee") else None,
            "nb_logements": int(item.get("nb_logmt_total", 0)),
            "categorie": item.get("bs"),
            "lat": item["geo_point_2d"]["lat"],
            "lon": item["geo_point_2d"]["lon"]
        })
    clean_and_save(cleaned, "logements_sociaux")

def transform_espaces_verts():
    """Extraction et typage des espaces verts."""
    path = os.path.join(BRONZE_DIR, "espaces_verts.json")
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        
    cleaned = []
    for item in raw:
        cp = str(item.get("adresse_codepostal", ""))
        arr = int(cp[-2:]) if cp.startswith("75") and len(cp) == 5 else 0
        
        lat, lon = None, None
        if item.get("geom_x_y"):
            lat, lon = item["geom_x_y"].get("lat"), item["geom_x_y"].get("lon")
            
        cleaned.append({
            "nom": item.get("nom_ev"),
            "categorie": item.get("categorie"),
            "surface": item.get("surface_totale_reelle", 0),
            "arrondissement": arr,
            "lat": lat,
            "lon": lon
        })
    clean_and_save(cleaned, "espaces_verts")

def transform_velib(arr_gdf):
    """Traitement des stations Vélib'."""
    path = os.path.join(BRONZE_DIR, "velib.json")
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        
    df = pd.DataFrame([{
        "nom": item.get("name"),
        "capacite": item.get("capacity"),
        "lat": item.get("coordonnees_geo", {}).get("lat"),
        "lon": item.get("coordonnees_geo", {}).get("lon")
    } for item in raw])
    
    df = assign_arrondissement(df, "lat", "lon", arr_gdf)
    df = df[df['arrondissement'] > 0]
    clean_and_save(df.to_dict(orient="records"), "velib")

def transform_common_points(dataset_name, name_field, lat_field, lon_field, arr_gdf, extra_fields=None):
    """Fonction générique pour le nettoyage de 'Point layers'."""
    path = os.path.join(BRONZE_DIR, f"{dataset_name}.json")
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        
    records = []
    for item in raw:
        lat = item
        for k in lat_field.split('.'): lat = lat.get(k, {}) if isinstance(lat, dict) else None
        
        lon = item
        for k in lon_field.split('.'): lon = lon.get(k, {}) if isinstance(lon, dict) else None
        
        if lat is None or lon is None: continue
        
        record = {
            "nom": item.get(name_field, "Inconnu"),
            "lat": float(lat),
            "lon": float(lon)
        }
        
        if extra_fields:
            for ex in extra_fields:
                record[ex] = item.get(ex)
        
        records.append(record)
        
    df = pd.DataFrame(records)
    if df.empty: return
    
    df = assign_arrondissement(df, "lat", "lon", arr_gdf)
    df = df[df['arrondissement'] > 0]
    
    clean_and_save(df.where(pd.notnull(df), None).to_dict(orient="records"), dataset_name)

def transform_data_gouv():
    """Nettoyage des fichiers CSV du portail Data.gouv.fr."""
    path = os.path.join(BRONZE_DIR, "monuments_historiques.csv")
    if os.path.exists(path):
        # Utilisation de l'underscore pour correspondre au header réel
        df = pd.read_csv(path, sep='|', on_bad_lines='skip', low_memory=False)
        
        # Filtre souple sur Paris (car peut être "Paris 01", "Paris 18e", etc.)
        df_paris = df[df['Commune_forme_index'].str.contains('Paris', na=False, case=False)].copy()
        
        records = []
        for _, row in df_paris.iterrows():
            coords = str(row.get('coordonnees_au_format_WGS84', ''))
            lat, lon = None, None
            if ',' in coords:
                parts = coords.split(',')
                if len(parts) == 2:
                    try:
                        lat, lon = float(parts[0].strip()), float(parts[1].strip())
                    except:
                        lat, lon = None, None
            
            records.append({
                "nom": row.get('Denomination_de_l_edifice', 'Inconnu'),
                "adresse": row.get('Adresse_forme_editoriale', ''),
                "lat": lat,
                "lon": lon
            })
        
        df_clean = pd.DataFrame(records)
        df_clean = df_clean.dropna(subset=['lat', 'lon'])
        
        arr_gdf = load_arrondissements()
        df_clean = assign_arrondissement(df_clean, "lat", "lon", arr_gdf)
        df_clean = df_clean[df_clean['arrondissement'] > 0]
        
        clean_and_save(df_clean.where(pd.notnull(df_clean), None).to_dict(orient="records"), "monuments_historiques")

def transform_air_quality():
    """Traitement des indices de qualité de l'air (ATMO)."""
    path = os.path.join(BRONZE_DIR, "qualite_air.json")
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        
    # On garde les mesures récentes (ex: indice ATMO du jour)
    # Ce dataset est global pour Paris, on l'utilisera comme constante pour tous les arrondissements
    clean_and_save(raw, "qualite_air")

def transform_culture_events(arr_gdf):
    """Traitement des événements culturels 'Que faire à Paris'."""
    path = os.path.join(BRONZE_DIR, "culture_events.json")
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        
    records = []
    for item in raw:
        gp = item.get("geo_point_2d")
        if not gp: continue
        
        records.append({
            "nom": item.get("title", "Événement"),
            "lieu": item.get("address_name", ""),
            "lat": gp.get("lat"),
            "lon": gp.get("lon"),
            "date_debut": item.get("date_start"),
            "date_fin": item.get("date_end")
        })
        
    df = pd.DataFrame(records)
    if df.empty: return
    
    df = assign_arrondissement(df, "lat", "lon", arr_gdf)
    df = df[df['arrondissement'] > 0]
    
    clean_and_save(df.to_dict(orient="records"), "culture_events")



def process_all():
    """Orchestre la phase Silver."""
    ensure_silver_dir()
    print("\n--- Starting Silver Phase Transformation ---")
    print("=" * 50)
    
    arr_gdf = load_arrondissements()
    
    transform_logements_sociaux()
    transform_espaces_verts()
    transform_velib(arr_gdf)
    
    transform_common_points("belib", "adresse_station", "coordonneesxy.lat", "coordonneesxy.lon", arr_gdf)
    transform_common_points("stationnement_emplacements", "typsta", "locsta.lat", "locsta.lon", arr_gdf, ["typsta", "parite"])
    transform_common_points("toilettes", "type", "geo_point_2d.lat", "geo_point_2d.lon", arr_gdf, ["acces_pmr"])
    transform_common_points("ecoles", "nom_etablissement", "geo_point_2d.lat", "geo_point_2d.lon", arr_gdf)
    transform_common_points("colleges", "nom_etablissement", "geo_point_2d.lat", "geo_point_2d.lon", arr_gdf)
    transform_common_points("marches", "nom", "geo_point_2d.lat", "geo_point_2d.lon", arr_gdf, ["jours_tenue"])
    transform_common_points("arbres", "libelle_francais", "geo_point_2d.lat", "geo_point_2d.lon", arr_gdf, ["stade_de_developpement"])
    transform_common_points("commerces", "enseigne", "geo_point_2d.lat", "geo_point_2d.lon", arr_gdf, ["libelle_activite_principale"])
    
    transform_data_gouv()
    transform_air_quality()
    transform_culture_events(arr_gdf)


    
    print("\nSilver Transformation Complete!")

if __name__ == "__main__":
    process_all()
