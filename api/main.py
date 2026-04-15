"""FastAPI · expose les données Gold au frontend"""
from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"

app = FastAPI(title="Urban Data Explorer API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INDICATORS = {
    "prix_m2_median": "Prix médian au m² (€)",
    "dynamique_immo_pct": "Variation prix m² sur 5 ans (%)",
    "tension_locative": "Indice de tension (1 = médiane Paris)",
    "mixite_sociale": "Score de mixité sociale (0-1)",
    "qualite_vie": "Qualité de vie (verts + vélib + écoles)",
}


@lru_cache(maxsize=1)
def _arr():
    p = GOLD / "arrondissements.geojson"
    if not p.exists():
        raise HTTPException(503, "Gold layer not built · run `python -m pipeline.run`")
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _ts():
    p = GOLD / "timeseries.parquet"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_parquet(p)


@app.get("/health")
def health():
    return {"status": "ok", "gold_ready": (GOLD / "arrondissements.geojson").exists()}


@app.get("/indicators")
def list_indicators():
    return INDICATORS


@app.get("/arrondissements")
def arrondissements():
    return JSONResponse(_arr())


@app.get("/arrondissements/{code}")
def one_arr(code: int):
    for f in _arr()["features"]:
        if int(f["properties"].get("code_ar", -1)) == code:
            return f
    raise HTTPException(404, f"arrondissement {code} not found")


@app.get("/timeseries/{code}")
def timeseries(code: int, indicator: str = "prix_m2_median"):
    df = _ts()
    if df.empty:
        raise HTTPException(503, "timeseries not built")
    if indicator not in df.columns:
        raise HTTPException(400, f"unknown indicator · available: {list(df.columns)}")
    sub = df[df["code_ar"] == code].sort_values("annee")
    return {
        "code_ar": code,
        "indicator": indicator,
        "points": sub[["annee", indicator]].rename(columns={indicator: "value"}).to_dict("records"),
    }


@app.get("/compare")
def compare(a: int, b: int):
    fa = one_arr(a)
    fb = one_arr(b)
    return {"a": fa["properties"], "b": fb["properties"]}


@app.get("/matrix/{indicator}")
def matrix(indicator: str = "prix_m2_median"):
    """Renvoie {year: {code_ar: value}} pour alimenter la timeline côté front."""
    df = _ts()
    if df.empty:
        raise HTTPException(503, "timeseries not built")
    if indicator not in df.columns:
        raise HTTPException(400, f"unknown indicator · available: {list(df.columns)}")
    out: dict[int, dict[int, float]] = {}
    for year, sub in df.groupby("annee"):
        out[int(year)] = {int(r.code_ar): float(getattr(r, indicator)) for r in sub.itertuples()}
    return {"indicator": indicator, "years": sorted(out.keys()), "data": out}
