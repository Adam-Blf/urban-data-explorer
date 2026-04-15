"""
Couche Gold (medallion architecture).

Rôle : assembler toutes les tables Silver dans une vue unique par arrondissement,
calculer les indicateurs composites exposés au frontend, et produire les
artefacts consommés par l'API :
  - `arrondissements.geojson` · contours + propriétés enrichies
  - `timeseries.parquet` · évolution annuelle par arrondissement

Indicateurs produits :
  1. prix_m2_median          · médiane DVF de l'année la plus récente
  2. dynamique_immo_pct      · variation % prix médian entre année la + ancienne et la + récente
  3. tension_locative        · prix normalisé (1 = médiane Paris)
  4. mixite_sociale          · densité logements sociaux / surface, normalisée
  5. qualite_vie             · moyenne normalisée (verts + vélib + écoles + sanisettes) / surface
  6. mobilite_douce          · densité (vélib + belib + cyclables) / surface
  7. service_public          · densité (écoles + collèges + marchés) / surface
"""
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
    # Chaque source silver optionnelle : si le parquet n'existe pas (source
    # downloadable en 404 ou erreur silver), on renvoie un DataFrame vide pour
    # que les merges restent no-op plutôt que de casser la pipeline.
    def _try(name, cols):
        try:
            return pd.read_parquet(SILVER / f"{name}.parquet")
        except FileNotFoundError:
            return pd.DataFrame(columns=cols)
    extras = {
        name: _try(name, ["code_ar", f"nb_{name}"])
        for name in ("espaces_verts", "velib", "ecoles", "colleges",
                     "marches", "sanisettes", "belib", "cyclables")
    }
    return ar, dvf, ls, extras


def build():
    GOLD.mkdir(parents=True, exist_ok=True)
    ar, dvf, ls, extras = _load()

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

    # Merge de toutes les sources silver optionnelles sur code_ar
    for frame in extras.values():
        if len(frame):
            ar = ar.merge(frame, on="code_ar", how="left")

    def _norm(s: pd.Series) -> pd.Series:
        """Min-max normalisation tolérante aux NaN (NaN → 0), renvoie [0, 1]."""
        m = s.max() or 1
        return (s.fillna(0) / m).astype(float)

    def _composite(cols: list[str]) -> pd.Series | None:
        """Moyenne des densités (nb/surface) normalisées ensuite à [0, 1]."""
        parts = [_norm(ar[c] / ar["surface"]) for c in cols if c in ar.columns]
        if not parts:
            return None
        agg = sum(parts) / len(parts)
        return (agg / (agg.max() or 1)).round(3)

    # Indicateur 3 · qualité de vie = aménités urbaines douces (verts/loisirs)
    ar["qualite_vie"] = _composite(
        ["nb_espaces_verts", "nb_velib", "nb_ecoles", "nb_sanisettes"]
    )
    # Indicateur 4 · mobilité douce = vélib + bornes électriques + pistes cyclables
    ar["mobilite_douce"] = _composite(
        ["nb_velib", "nb_belib", "nb_cyclables"]
    )
    # Indicateur 5 · service public = équipements éducation & commerce de proximité
    ar["service_public"] = _composite(
        ["nb_ecoles", "nb_colleges", "nb_marches"]
    )

    # Export GeoJSON pour l'API
    out_geo = GOLD / "arrondissements.geojson"
    ar.to_file(out_geo, driver="GeoJSON")
    print(f"[gold] {out_geo}")
    print(f"[gold] timeseries · {GOLD / 'timeseries.parquet'}")
    return out_geo


if __name__ == "__main__":
    build()
