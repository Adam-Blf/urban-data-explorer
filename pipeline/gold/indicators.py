"""Gold · jointures + 4 indicateurs composites prêts pour l'API"""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"


def _load():
    ar = gpd.read_parquet(SILVER / "arrondissements.parquet")
    dvf = pd.read_parquet(SILVER / "dvf.parquet")
    try:
        ls = pd.read_parquet(SILVER / "logements_sociaux.parquet")
    except FileNotFoundError:
        ls = pd.DataFrame(columns=["code_ar"])
    def _try(name, cols):
        try:
            return pd.read_parquet(SILVER / f"{name}.parquet")
        except FileNotFoundError:
            return pd.DataFrame(columns=cols)
    ev = _try("espaces_verts", ["code_ar", "nb_espaces_verts"])
    vb = _try("velib", ["code_ar", "nb_velib"])
    ec = _try("ecoles", ["code_ar", "nb_ecoles"])
    return ar, dvf, ls, ev, vb, ec


def build():
    GOLD.mkdir(parents=True, exist_ok=True)
    ar, dvf, ls, ev, vb, ec = _load()

    # prix m² courant (dernière année dispo)
    last_year = int(dvf["annee"].max())
    prix_current = (
        dvf[dvf["annee"] == last_year]
        .groupby("code_ar")["prix_m2"]
        .median()
        .rename("prix_m2_median")
    )

    # prix m² année la plus ancienne dispo → dynamique
    first_year = int(dvf["annee"].min())
    prix_past = (
        dvf[dvf["annee"] == first_year]
        .groupby("code_ar")["prix_m2"]
        .median()
        .rename("prix_m2_past")
    )
    dyn = ((prix_current - prix_past) / prix_past * 100).rename("dynamique_immo_pct")

    # proxy logements sociaux (si dispo)
    if "code_ar" in ls.columns and len(ls):
        pls = ls.groupby("code_ar").size().rename("nb_logements_sociaux")
    else:
        pls = pd.Series(dtype=float, name="nb_logements_sociaux")

    # Timeseries annuelle par arrondissement
    ts = (
        dvf.groupby(["code_ar", "annee"])
        .agg(prix_m2_median=("prix_m2", "median"), n_ventes=("prix_m2", "size"))
        .reset_index()
    )
    ts.to_parquet(GOLD / "timeseries.parquet", index=False)

    # Assemblage arrondissements
    ar = ar.merge(prix_current, on="code_ar", how="left")
    ar = ar.merge(dyn, on="code_ar", how="left")
    ar = ar.merge(pls, on="code_ar", how="left")

    # Indicateur 1 · tension locative (proxy sans revenu médian → prix normalisé)
    ar["tension_locative"] = (ar["prix_m2_median"] / ar["prix_m2_median"].median()).round(2)

    # Indicateur 2 · mixité sociale (densité normalisée, fallback si manquant)
    if "surface" in ar.columns and ar["nb_logements_sociaux"].notna().any():
        ar["mixite_sociale"] = (ar["nb_logements_sociaux"] / ar["surface"]).fillna(0)
        m = ar["mixite_sociale"].max() or 1
        ar["mixite_sociale"] = (ar["mixite_sociale"] / m).round(3)
    else:
        ar["mixite_sociale"] = None

    # Indicateur 3 · qualité de vie composite = moyenne normalisée (espaces verts + vélib + écoles) / surface
    for frame in (ev, vb, ec):
        if len(frame):
            ar = ar.merge(frame, on="code_ar", how="left")

    def _norm(s: pd.Series) -> pd.Series:
        m = s.max() or 1
        return (s.fillna(0) / m).astype(float)

    parts = [
        _norm(ar[col] / ar["surface"])
        for col in ("nb_espaces_verts", "nb_velib", "nb_ecoles")
        if col in ar.columns
    ]
    if parts:
        composite = sum(parts) / len(parts)
        ar["qualite_vie"] = (composite / (composite.max() or 1)).round(3)
    else:
        ar["qualite_vie"] = None

    # Export GeoJSON pour l'API
    out_geo = GOLD / "arrondissements.geojson"
    ar.to_file(out_geo, driver="GeoJSON")
    print(f"[gold] {out_geo}")
    print(f"[gold] timeseries · {GOLD / 'timeseries.parquet'}")
    return out_geo


if __name__ == "__main__":
    build()
