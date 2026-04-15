"""Silver · nettoyage + normalisation → parquet"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Use pyogrio engine (avoids fiona API drift)
gpd.options.io_engine = "pyogrio"

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data" / "bronze"
SILVER = ROOT / "data" / "silver"


def _latest(src: str, ext: str) -> Path:
    files = sorted((BRONZE / src).glob(f"*.{ext}"))
    if not files:
        raise FileNotFoundError(f"no bronze file for {src}.{ext}")
    return files[-1]


def arrondissements() -> Path:
    gdf = gpd.read_file(_latest("arrondissements", "geojson"))
    # harmonise la clé
    code_col = next(c for c in ["c_ar", "c_arinsee", "arrondissement"] if c in gdf.columns)
    gdf = gdf.rename(columns={code_col: "code_ar"})
    gdf["code_ar"] = gdf["code_ar"].astype(int)
    keep = ["code_ar", "l_ar", "surface", "perimetre", "geometry"]
    gdf = gdf[[c for c in keep if c in gdf.columns]]
    out = SILVER / "arrondissements.parquet"
    SILVER.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(out)
    print(f"[silver] {out} · {len(gdf)} rows")
    return out


def dvf() -> Path:
    frames = []
    for src in sorted((BRONZE).glob("dvf_*")):
        f = sorted(src.glob("*.csv.gz"))
        if not f:
            continue
        frames.append(pd.read_csv(f[-1], low_memory=False, compression="gzip"))
    if not frames:
        raise FileNotFoundError("no dvf_* bronze file")
    df = pd.concat(frames, ignore_index=True)
    df = df[df["nature_mutation"] == "Vente"].copy()
    df = df[df["type_local"].isin(["Appartement", "Maison"])]
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "code_postal"])
    df = df[df["surface_reelle_bati"] > 9]
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]
    df = df[df["prix_m2"].between(1000, 50000)]
    df["code_ar"] = (df["code_postal"].astype(int) - 75000).clip(1, 20)
    df["annee"] = pd.to_datetime(df["date_mutation"]).dt.year
    out = SILVER / "dvf.parquet"
    df[["code_ar", "annee", "prix_m2", "surface_reelle_bati", "type_local"]].to_parquet(out)
    print(f"[silver] {out} · {len(df)} rows")
    return out


def logements_sociaux() -> Path:
    raw = json.loads(_latest("logements_sociaux", "json").read_text(encoding="utf-8"))
    df = pd.DataFrame(raw)
    # garder seulement les colonnes scalaires (DVF + parquet n'aime pas les structs vides)
    df = df.select_dtypes(include=["number", "object", "bool"]).copy()
    for c in list(df.columns):
        if df[c].map(lambda v: isinstance(v, (dict, list))).any():
            df = df.drop(columns=[c])
    src_col = next((c for c in ["arrdt", "arrondissement", "code_postal"] if c in df.columns), None)
    if src_col == "code_postal":
        df["code_ar"] = (df[src_col].astype(float).astype(int) - 75000).clip(1, 20)
    elif src_col:
        df["code_ar"] = pd.to_numeric(df[src_col].astype(str).str.extract(r"(\d+)")[0], errors="coerce").astype("Int64")
    out = SILVER / "logements_sociaux.parquet"
    df.to_parquet(out)
    print(f"[silver] {out} · {len(df)} rows")
    return out


def espaces_verts() -> Path:
    """Spatial join: count + surface verte par arrondissement."""
    gv = gpd.read_file(_latest("espaces_verts", "geojson"))
    ar = gpd.read_parquet(SILVER / "arrondissements.parquet")
    if gv.crs is None:
        gv.set_crs(epsg=4326, inplace=True)
    gv = gv.to_crs(ar.crs)
    # centroid-based join (tolerant to invalid geometries)
    gv["geometry"] = gv.geometry.representative_point()
    joined = gpd.sjoin(gv, ar[["code_ar", "geometry"]], how="inner", predicate="within")
    agg = joined.groupby("code_ar").size().rename("nb_espaces_verts").reset_index()
    out = SILVER / "espaces_verts.parquet"
    agg.to_parquet(out, index=False)
    print(f"[silver] {out} · {len(agg)} rows")
    return out


def _count_per_ar(src_name: str, ext: str, label: str) -> Path:
    gv = gpd.read_file(_latest(src_name, ext))
    ar = gpd.read_parquet(SILVER / "arrondissements.parquet")
    if gv.crs is None:
        gv.set_crs(epsg=4326, inplace=True)
    gv = gv.to_crs(ar.crs)
    gv["geometry"] = gv.geometry.representative_point()
    joined = gpd.sjoin(gv, ar[["code_ar", "geometry"]], how="inner", predicate="within")
    agg = joined.groupby("code_ar").size().rename(f"nb_{label}").reset_index()
    out = SILVER / f"{label}.parquet"
    agg.to_parquet(out, index=False)
    print(f"[silver] {out} · {len(agg)} rows")
    return out


def velib() -> Path:
    return _count_per_ar("velib_stations", "geojson", "velib")


def ecoles() -> Path:
    return _count_per_ar("ecoles_elementaires", "geojson", "ecoles")


def run():
    arrondissements()
    dvf()
    for fn in (logements_sociaux, espaces_verts, velib, ecoles):
        try:
            fn()
        except Exception as e:
            print(f"[silver] {fn.__name__} skipped: {e}")


if __name__ == "__main__":
    run()
