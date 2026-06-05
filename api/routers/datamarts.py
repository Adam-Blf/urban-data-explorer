from __future__ import annotations
from fastapi import APIRouter, Query
from ..data import city_overview, district_rows, timeline_rows, geojson_by_granularity
from ..schemas import DistrictRow, Overview, TimelinePoint

router = APIRouter(prefix="/datamarts", tags=["datamarts"])


@router.get("/dashboard", response_model=list[DistrictRow])
def dashboard(
    arrondissement: str | None = Query(None, description="Filtre par code (ex : 75011)"),
    score_min: int | None = Query(None, ge=0, le=100, description="Score global minimum"),
    sort: str = Query("code", pattern="^(code|score)$", description="Tri : code ou score"),
):
    """Datamart filtrable : par arrondissement, score minimum, avec tri.

    Repond a l'attendu enonce d'une API filtrable (par secteur / categorie)."""
    rows = district_rows()
    if arrondissement:
        rows = [r for r in rows if r.get("code") == arrondissement]
    if score_min is not None:
        rows = [r for r in rows if r.get("score", 0) >= score_min]
    if sort == "score":
        rows = sorted(rows, key=lambda r: r.get("score", 0), reverse=True)
    return [DistrictRow(**row) for row in rows]


@router.get("/overview", response_model=Overview)
def overview():
    return Overview(**city_overview())


@router.get("/timeline", response_model=list[TimelinePoint])
def timeline():
    return [TimelinePoint(**row) for row in timeline_rows()]


@router.get("/geojson/{level}")
def get_geojson(level: int):
    """Retourne le GeoJSON selon le niveau de granularité (0-4)."""
    return geojson_by_granularity(level)
