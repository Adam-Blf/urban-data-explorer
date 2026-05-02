"""Source · POI (Points d'Intérêt) Paris OpenData génériques.

Beaucoup de datasets Paris OpenData partagent la même API Explore v2.1
(Vélib stations, Belib bornes, écoles, sanisettes, marchés...). Ce module
factorise leur ingestion via un dictionnaire de configuration `POI_REGISTRY`.

Chaque entrée déclare :
- `dataset_id` : identifiant Paris OpenData
- `category`   : catégorie logique pour le datamart (transport, sante, ...)
- `subcategory`: étiquette plus fine (velib, belib, ecole, ...)

Sources data.gouv (musées, hôpitaux, monuments) sont gérées séparément.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import httpx
import polars as pl


@dataclass(frozen=True)
class PoiSource:
    dataset_id: str
    category: str
    subcategory: str


POI_REGISTRY: dict[str, PoiSource] = {
    # --- Transport ---
    "velib_stations": PoiSource(
        "velib-emplacement-des-stations", "transport", "velib"
    ),
    "belib_bornes": PoiSource(
        "belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel",
        "transport",
        "borne_electrique",
    ),
    "amenagements_cyclables": PoiSource(
        "amenagements-cyclables", "transport", "piste_cyclable"
    ),
    # --- Service public ---
    "ecoles_elementaires": PoiSource(
        "etablissements-scolaires-ecoles-elementaires",
        "service_public",
        "ecole",
    ),
    "colleges": PoiSource(
        "etablissements-scolaires-colleges", "service_public", "college"
    ),
    # --- Commerce ---
    "marches": PoiSource(
        "marches-decouverts", "commerce", "marche"
    ),
    # --- Culture ---
    "que_faire_paris": PoiSource(
        "que-faire-a-paris-", "culture", "evenement"
    ),
    # --- Environnement ---
    "espaces_verts": PoiSource(
        "espaces_verts", "environnement", "espace_vert"
    ),
    "sanisettes": PoiSource(
        "sanisettesparis", "service_public", "sanisette"
    ),
}


def fetch(
    poi_key: str,
    raw_partition_dir: Path,
    paris_opendata_base_url: str,
    logger: logging.Logger,
    page_size: int = 100,
    max_records: int = 50_000,
) -> Path:
    """Pagine l'API Paris OpenData Explore v2.1 pour le dataset demandé."""
    if poi_key not in POI_REGISTRY:
        raise KeyError(f"unknown POI key: {poi_key} · valid={list(POI_REGISTRY)}")
    src = POI_REGISTRY[poi_key]

    raw_partition_dir.mkdir(parents=True, exist_ok=True)
    out = raw_partition_dir / f"{poi_key}.parquet"
    url = f"{paris_opendata_base_url}/{src.dataset_id}/records"

    rows: list[dict] = []
    offset = 0
    with httpx.Client(timeout=120.0) as client:
        while offset < max_records:
            params = {"limit": page_size, "offset": offset}
            logger.info("%s · GET offset=%d", poi_key, offset)
            try:
                resp = client.get(url, params=params)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.error("%s · HTTP error: %s · stopping pagination", poi_key, e)
                break
            payload = resp.json()
            results = payload.get("results", [])
            if not results:
                break
            rows.extend(results)
            offset += len(results)
            if len(results) < page_size:
                break

    if not rows:
        logger.error("%s · empty response · writing empty parquet for idempotence", poi_key)
        df = pl.DataFrame({
            "category": pl.Series([], dtype=pl.Utf8),
            "subcategory": pl.Series([], dtype=pl.Utf8),
        })
    else:
        df = pl.from_dicts(rows, infer_schema_length=2_000)
        df = df.with_columns([
            pl.lit(src.category).alias("category"),
            pl.lit(src.subcategory).alias("subcategory"),
        ])

    df.write_parquet(out, compression="snappy")
    logger.info("%s · wrote %s (%d rows)", poi_key, out, df.height)
    return out
