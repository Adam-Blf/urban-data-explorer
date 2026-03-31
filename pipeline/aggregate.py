import os
import json
import pandas as pd
from config import BASE_DIR, SILVER_DIR, GOLD_DIR, BRONZE_DIR

def ensure_gold_dir():
    if not os.path.exists(GOLD_DIR):
        os.makedirs(GOLD_DIR)
        print(f"📁 Création du répertoire: {GOLD_DIR}")

def load_silver(name):
    path = os.path.join(SILVER_DIR, f"{name}.json")
    if not os.path.exists(path):
        return pd.DataFrame() # Retourne un DF vide
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return pd.DataFrame(data)

def normalize_series(series):
    """Normalise une série Pandas entre 0 et 100."""
    if series.empty or series.max() == series.min():
        return pd.Series(0, index=series.index)
    return ((series - series.min()) / (series.max() - series.min())) * 100

def generate_realistic_dvf():
    """Génère des prix au m2 réalistes pour Paris (2024)."""
    # Données moyennées réalistes pour l'année 2024
    prices = {
        1: 12500, 2: 11500, 3: 12000, 4: 12800, 5: 12100,
        6: 14500, 7: 13500, 8: 11800, 9: 10500, 10: 9500,
        11: 9800, 12: 9200, 13: 8800, 14: 9900, 15: 9700,
        16: 11200, 17: 10400, 18: 9100, 19: 8200, 20: 8400
    }
    return pd.Series(prices, name="prix_m2")

def compute_indicators():
    print("\n🏆 Démarrage de la Phase Gold (Agrégation)")
    print("=" * 50)
    ensure_gold_dir()
    
    # Initialisation DataFrame des arrondissements (1 à 20)
    df_arr = pd.DataFrame(index=range(1, 21))
    df_arr.index.name = "arrondissement"
    
    # ---- Chargement et agrégation des données Silver ----
    
    # 1. Espaces verts
    df_ev = load_silver("espaces_verts")
    if not df_ev.empty:
        df_arr['ev_surface'] = df_ev.groupby("arrondissement")["surface"].sum()
    else:
        df_arr['ev_surface'] = 0
        
    # 2. Toilettes, Ecoles, Marches
    for ds_name, target_col in [("toilettes", "nb_toilettes"), 
                               ("ecoles", "nb_ecoles"), 
                               ("marches", "nb_marches")]:
        df = load_silver(ds_name)
        if not df.empty:
            df_arr[target_col] = df.groupby("arrondissement").size()
        else:
            df_arr[target_col] = 0
            
    # 3. Velib, Belib, Stationnement
    df_velib = load_silver("velib")
    if not df_velib.empty:
        df_arr['velib_stations'] = df_velib.groupby("arrondissement").size()
        df_arr['velib_capacite'] = df_velib.groupby("arrondissement")['capacite'].sum()
    else:
        df_arr['velib_stations'] = 0
        df_arr['velib_capacite'] = 0

    df_belib = load_silver("belib")
    df_arr['nb_belib'] = df_belib.groupby("arrondissement").size() if not df_belib.empty else 0
    
    df_stat = load_silver("stationnement_emplacements")
    df_arr['nb_parking'] = df_stat.groupby("arrondissement").size() if not df_stat.empty else 0
    
    # 4. Monuments et Musées
    df_monument = load_silver("monuments_historiques")
    df_arr['nb_monuments'] = df_monument.groupby("arrondissement").size() if not df_monument.empty else 0
    
    # Actuellement la phase silver pour musées n'est pas encore faite, on utilise 0 ou la source
    df_arr['nb_musees'] = 0 
    
    # 5. Logements Sociaux
    df_ls = load_silver("logements_sociaux")
    if not df_ls.empty:
        df_arr['logements_sociaux'] = df_ls.groupby("arrondissement")["nb_logements"].sum()
    else:
        df_arr['logements_sociaux'] = 0
        
    # Remplaçage des NaN par 0
    df_arr = df_arr.fillna(0)
    
    # 6. DVF (Prix de l'immobilier mocké de manière réaliste)
    df_dvf = generate_realistic_dvf()
    df_arr = df_arr.join(df_dvf)
    
    print("Calcul des indicateurs composites...")
    
    # ======== CALCUL DES INDICATEURS COMPOSITES (0 - 100) ========
    
    # 🌿 1. Indice de Qualité de Vie (Espaces verts + Services + Écoles + Marchés)
    # Les poids: Espaces verts (40%), Écoles (30%), Marches (15%), Toilettes (15%)
    idx_ev = normalize_series(df_arr['ev_surface']) * 0.4
    idx_ec = normalize_series(df_arr['nb_ecoles']) * 0.3
    idx_ma = normalize_series(df_arr['nb_marches']) * 0.15
    idx_to = normalize_series(df_arr['nb_toilettes']) * 0.15
    df_arr['indice_qdv'] = (idx_ev + idx_ec + idx_ma + idx_to).round(1)
    
    # 🚗 2. Indice de Mobilité Urbaine (Vélib + Belib + Stationnement)
    # Poids: Velib capacité (50%), Belib (30%), Parking (20%)
    idx_vk = normalize_series(df_arr['velib_capacite']) * 0.5
    idx_be = normalize_series(df_arr['nb_belib']) * 0.3
    idx_pa = normalize_series(df_arr['nb_parking']) * 0.2
    df_arr['indice_mobilite'] = (idx_vk + idx_be + idx_pa).round(1)
    
    # 🏛️ 3. Indice de Patrimoine Culturel (Monuments)
    idx_mo = normalize_series(df_arr['nb_monuments'])
    df_arr['indice_culture'] = idx_mo.round(1)
    
    # 🏘️ 4. Indice de Tension Immobilière
    # Plus de logements sociaux => Baisse la tension
    # Prix élevés => Hausse la tension
    # Tension max = 100 (Prix très haut, peu de logements sociaux)
    norm_prix = normalize_series(df_arr['prix_m2'])
    norm_ls = normalize_series(df_arr['logements_sociaux']) # 0 = Peu, 100 = Beaucoup
    # Formule combinée : 70% prix, 30% manque de logements sociaux
    idx_tension = (norm_prix * 0.7) + ((100 - norm_ls) * 0.3)
    df_arr['indice_tension'] = idx_tension.round(1)
    
    # Export en JSON classique (dict index par arrondissement)
    gold_data = df_arr.to_dict(orient="index")
    out_json = os.path.join(GOLD_DIR, "indicateurs.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(gold_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Indicateurs exportés: {out_json}")
    
    # Fusionner avec le GeoJSON des arrondissements pour le rendre lisible directement par la map
    geojson_path = os.path.join(BRONZE_DIR, "arrondissements.geojson")
    if os.path.exists(geojson_path):
        import geopandas as gpd
        gdf = gpd.read_file(geojson_path)
        
        # Mapping de l'arrondissement
        col_ar = 'c_ar' if 'c_ar' in gdf.columns else 'c_arint'
        gdf['arrondissement'] = gdf[col_ar].astype(int)
        
        # Merge de df_arr dans gdf
        gdf_merged = gdf.merge(df_arr, left_on='arrondissement', right_index=True, how='left')
        
        out_geojson = os.path.join(GOLD_DIR, "arrondissements_stats.geojson")
        gdf_merged.to_file(out_geojson, driver="GeoJSON")
        print(f"✅ GeoJSON complet exporté: {out_geojson}")
    
    print("\n✨ Agrégation Gold terminée!")

if __name__ == "__main__":
    compute_indicators()
    
