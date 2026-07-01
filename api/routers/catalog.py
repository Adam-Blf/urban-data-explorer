"""Router /catalog – exposition du catalogue des 82 sources Open Data.

Route :
- GET /catalog/sources : liste des sources, filtrables par famille
  (mobilite, vie_quotidienne, environnement, logement_urbanisme).
  Retourne les metadonnees de chaque SourceSpec (id, titre, provider, URL catalogue).
"""

from __future__ import annotations
from fastapi import APIRouter
from ..data import source_catalog
from ..schemas import SourceRow

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/sources", response_model=list[SourceRow])
def sources(family: str | None = None):
    rows = source_catalog()
    if family and family != "all":
        rows = [r for r in rows if r["family"] == family]
    return [SourceRow(**r) for r in rows]
