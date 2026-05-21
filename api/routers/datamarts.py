from __future__ import annotations
from fastapi import APIRouter
from ..data import city_overview, district_rows, timeline_rows, geojson_by_granularity
from ..schemas import DistrictRow, Overview, TimelinePoint

router = APIRouter(prefix="/datamarts", tags=["datamarts"])


@router.get("/dashboard", response_model=list[DistrictRow])
def dashboard():
    return [DistrictRow(**row) for row in district_rows()]


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
