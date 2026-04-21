"""
Phase Gold : Analytics et Agrégation des Indicateurs
Auteur : Arnaud DISSONGO (Panason1c)
Rôle : Calcul des 4 indicateurs composites (Qualité de vie, Mobilité, Patrimoine, Tension).
       Génération du GeoJSON final enrichi pour la cartographie.
"""

import os
import json
import pandas as pd
import geopandas as gpd
from config import SILVER_DIR, GOLD_DIR, BRONZE_DIR

def ensure_gold_dir():
    """Crée le répertoire data/gold si nécessaire."""
    if not os.path.exists(GOLD_DIR):
        os.makedirs(GOLD_DIR)
        print(f"Creating directory: {GOLD_DIR}")

def load_silver_json(name):
    """Charge un dataset Silver en DataFrame et assure la présence du champ arrondissement."""
    path = os.path.join(SILVER_DIR, f"{name}.json")
    if not os.path.exists(path):
        return pd.DataFrame(columns=['arrondissement'])
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        df = pd.DataFrame(data)
        if 'arrondissement' not in df.columns:
            df['arrondissement'] = 0
        return df

def calculate_indicators():
    """
    Calcule les 4 indices composites par arrondissement.
    """
    print("\n--- Analytics: Calculating Gold Indicators ---")
    
    stats = {str(i): {
        "qualite_vie": 0, "mobilite": 0, "patrimoine": 0, "tension": 0,
        "details": {}
    } for i in range(1, 21)}
    
    # 1. QUALITÉ DE VIE (Espaces verts + Arbres + Air)
    df_ev = load_silver_json("espaces_verts")
    df_ecoles = load_silver_json("ecoles")
    df_marches = load_silver_json("marches")
    df_arbres = load_silver_json("arbres")
    df_air = load_silver_json("qualite_air")
    
    # Calcul de l'indice air moyen (on suppose un score global pour Paris)
    air_score = 70 # Valeur par défaut
    if not df_air.empty:
        # On pourrait moyenner les dernières valeurs, ici on simule une influence positive
        air_score = 85 

    for arr in stats:
        ev_count = len(df_ev[df_ev['arrondissement'] == int(arr)])
        ecole_count = len(df_ecoles[df_ecoles['arrondissement'] == int(arr)])
        march_count = len(df_marches[df_marches['arrondissement'] == int(arr)])
        tree_count = len(df_arbres[df_arbres['arrondissement'] == int(arr)])
        
        score = (ev_count * 2) + (ecole_count * 1.5) + (march_count * 3) + (tree_count * 0.05) + (air_score * 0.2)
        stats[arr]["qualite_vie"] = min(100, int(score))
        stats[arr]["details"]["espaces_verts"] = ev_count
        stats[arr]["details"]["arbres"] = tree_count
        stats[arr]["details"]["qualite_air"] = air_score


    # 2. MOBILITÉ (Vélib + Bornes Belib)
    df_velib = load_silver_json("velib")
    df_belib = load_silver_json("belib")
    
    for arr in stats:
        v_count = len(df_velib[df_velib['arrondissement'] == int(arr)])
        b_count = len(df_belib[df_belib['arrondissement'] == int(arr)])
        score = (v_count * 0.5) + (b_count * 5)
        stats[arr]["mobilite"] = min(100, int(score))
        stats[arr]["details"]["velib"] = v_count
        stats[arr]["details"]["bornes_electriques"] = b_count

    # 3. PATRIMOINE & CULTURE (Monuments + Événements)
    df_monum = load_silver_json("monuments_historiques")
    df_events = load_silver_json("culture_events")
    
    for arr in stats:
        m_count = len(df_monum[df_monum['arrondissement'] == int(arr)])
        e_count = len(df_events[df_events['arrondissement'] == int(arr)])
        score = (m_count * 4) + (e_count * 2)
        stats[arr]["patrimoine"] = min(100, int(score))
        stats[arr]["details"]["monuments"] = m_count
        stats[arr]["details"]["evenements"] = e_count

    # 4. DYNAMISME & TENSION (Logements Sociaux + Commerces)
    df_soc = load_silver_json("logements_sociaux")
    df_shop = load_silver_json("commerces")
    
    avg_prices = {
        "1": 12500, "2": 11800, "3": 12200, "4": 12800, "5": 12400, "6": 14500, "7": 13900, "8": 11500, "9": 11200, "10": 10200,
        "11": 10500, "12": 9500, "13": 9200, "14": 10100, "15": 10400, "16": 11200, "17": 10800, "18": 9400, "19": 8500, "20": 8800
    }

    for arr in stats:
        soc_count = df_soc[df_soc['arrondissement'] == int(arr)]['nb_logements'].sum() if not df_soc.empty else 0
        shop_count = len(df_shop[df_shop['arrondissement'] == int(arr)])
        price = avg_prices.get(arr, 10000)
        
        score = (price / 200) - (soc_count / 1000) + (shop_count / 100)
        stats[arr]["tension"] = max(0, min(100, int(score)))
        stats[arr]["details"]["prix_m2"] = price
        stats[arr]["details"]["commerces"] = shop_count
        stats[arr]["details"]["logements_sociaux"] = int(soc_count)



    with open(os.path.join(GOLD_DIR, "indicateurs.json"), 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        
    return stats

def generate_gold_geojson(indicators_dict):
    """
    Produit le GeoJSON final enrichi.
    """
    print("Map Layer: Generating Gold GeoJSON...")
    path_arr = os.path.join(BRONZE_DIR, "arrondissements.geojson")
    if not os.path.exists(path_arr):
        print("ERROR: missing base GeoJSON in Bronze.")
        return
        
    try:
        gdf = gpd.read_file(path_arr)
    except Exception as e:
        print(f"Warning: gpd.read_file failed ({e}). Fallback to JSON.")
        with open(path_arr, 'r', encoding='utf-8') as f:
            data = json.load(f)
        gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
    
    if 'c_ar' in gdf.columns:
        gdf['num_arr'] = gdf['c_ar'].astype(str)
    elif 'c_arint' in gdf.columns:
        gdf['num_arr'] = gdf['c_arint'].astype(str)
        
    def get_stats(row):
        try:
            arr_id = str(int(float(row['num_arr'])))
            ind = indicators_dict.get(arr_id, {})
            return pd.Series([ind.get("qualite_vie", 0), ind.get("mobilite", 0), ind.get("patrimoine", 0), ind.get("tension", 0)])
        except:
            return pd.Series([0, 0, 0, 0])
    
    gdf[['score_vie', 'score_mob', 'score_pat', 'score_ten']] = gdf.apply(get_stats, axis=1)
    gdf.to_file(os.path.join(GOLD_DIR, "arrondissements_stats.geojson"), driver='GeoJSON')
    print("Gold Layer Ready!")

def process_all():
    """Point d'entrée pour la phase Gold."""
    ensure_gold_dir()
    print("\nStarting Phase Gold (Analytics)")
    print("=" * 50)
    indicators = calculate_indicators()
    generate_gold_geojson(indicators)
    print("\nPhase Gold complete!")

if __name__ == "__main__":
    process_all()
