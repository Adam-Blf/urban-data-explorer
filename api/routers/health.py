from __future__ import annotations
from fastapi import APIRouter
from ..data import city_overview

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    overview = city_overview()
    return {
        "status": "ok",
        "mode": "local-first",
        "districts": overview["district_count"],
        "sources": overview["source_count"],
    }
