"""Chargeurs de sources externes reelles : DVF (prix immobilier) et INSEE Filosofi (revenus).

Ces deux sources alimentent le datamart Gold avec des valeurs reelles, en
remplacement des valeurs de reference codees en dur. Si les fichiers ne sont
pas presents (mode hors ligne sans telechargement), les chargeurs renvoient un
dictionnaire vide et le pipeline retombe sur les valeurs de reference.

Telechargement (documente dans le README) :
    DVF 75 2023 :
        https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/75.csv.gz
        -> data/raw/downloads/dvf_75_2023.csv.gz
    INSEE Filosofi IRIS 2020 :
        https://www.insee.fr/fr/statistiques/fichier/7233950/BASE_TD_FILO_DISP_IRIS_2020_CSV.zip
        -> data/raw/downloads/filosofi_iris_2020.zip
"""

from __future__ import annotations

import csv
import gzip
import io
import statistics
import zipfile
from pathlib import Path

# parents[2] : ce module vit dans etl/bronze/, 2 niveaux sous la racine repo.
ROOT = Path(__file__).resolve().parents[2]
DOWNLOADS = ROOT / "data" / "raw" / "downloads"

DVF_PATH = DOWNLOADS / "dvf_75_2023.csv.gz"
FILOSOFI_PATH = DOWNLOADS / "filosofi_iris_2020.zip"


def _arr_from_cp(code_postal: str) -> str | None:
    """75001..75020 -> code arrondissement normalise (750xx)."""
    cp = (code_postal or "").strip().split(".")[0]
    if len(cp) == 5 and cp.startswith("750"):
        try:
            n = int(cp[3:])
            if 1 <= n <= 20:
                return f"750{n:02d}"
        except ValueError:
            return None
    return None


def _arr_from_iris(iris: str) -> str | None:
    """Code IRIS INSEE (commune 751xx + iris) -> arrondissement 750xx."""
    iris = (iris or "").strip()
    if len(iris) >= 5 and iris.startswith("751"):
        try:
            n = int(iris[3:5])
            if 1 <= n <= 20:
                return f"750{n:02d}"
        except ValueError:
            return None
    return None


def load_dvf_prices() -> dict[str, dict[str, float]]:
    """Lit les vraies transactions immobilieres (DVF 2023) et calcule, par
    arrondissement : le prix median au m2 et le nombre de ventes.

    Etapes : ouvrir le .csv.gz -> garder appartements/maisons -> prix = valeur / surface
    -> ecarter les valeurs aberrantes -> mediane par arrondissement.
    Returns: {code: {"prix_m2": float, "sales_volume": int}}
    """
    if not DVF_PATH.exists():
        return {}

    by_arr: dict[str, list[float]] = {}
    volume: dict[str, int] = {}

    with gzip.open(DVF_PATH, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("type_local") not in ("Appartement", "Maison"):
                continue
            code = _arr_from_cp(row.get("code_postal", ""))
            if not code:
                continue
            try:
                val = float(row.get("valeur_fonciere") or 0)
                surf = float(row.get("surface_reelle_bati") or 0)
            except ValueError:
                continue
            if val <= 0 or surf < 9:  # surface plancher pour ecarter le bruit
                continue
            prix_m2 = val / surf
            if 1500 <= prix_m2 <= 40000:  # garde-fou contre les valeurs aberrantes
                by_arr.setdefault(code, []).append(prix_m2)
                volume[code] = volume.get(code, 0) + 1

    return {
        code: {"prix_m2": round(statistics.median(vals), 1), "sales_volume": volume[code]}
        for code, vals in by_arr.items()
        if vals
    }


def load_filosofi_income() -> dict[str, float]:
    """Lit le vrai revenu median des menages (INSEE Filosofi 2020, colonne DISP_MED20)
    par quartier IRIS, puis l'agrege par arrondissement (mediane des IRIS).

    Etapes : ouvrir le .zip -> lire le CSV -> code IRIS 751xx -> arrondissement
    -> mediane des revenus IRIS de l'arrondissement.
    Returns: {code: revenu_median_euro_annuel}
    """
    if not FILOSOFI_PATH.exists():
        return {}

    by_arr: dict[str, list[float]] = {}

    with zipfile.ZipFile(FILOSOFI_PATH) as z:
        csv_name = next(
            (n for n in z.namelist() if n.lower().endswith(".csv") and "meta" not in n.lower()),
            None,
        )
        if not csv_name:
            return {}
        text = z.read(csv_name).decode("latin-1", errors="replace")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        for row in reader:
            code = _arr_from_iris(row.get("IRIS", ""))
            if not code:
                continue
            raw = (row.get("DISP_MED20") or "").replace(",", ".").strip()
            try:
                med = float(raw)
            except ValueError:
                continue
            if med > 0:
                by_arr.setdefault(code, []).append(med)

    return {
        code: round(statistics.median(vals), 0)
        for code, vals in by_arr.items()
        if vals
    }


if __name__ == "__main__":
    dvf = load_dvf_prices()
    filo = load_filosofi_income()
    print(f"DVF arrondissements: {len(dvf)}")
    for c in sorted(dvf)[:5]:
        print("  ", c, dvf[c])
    print(f"Filosofi arrondissements: {len(filo)}")
    for c in sorted(filo)[:5]:
        print("  ", c, filo[c])
