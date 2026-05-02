"""Feeder · Bronze layer.

Ingestion paramétrable, sans chemin codé en dur. Partitionnement
`year=YYYY/month=MM/day=DD` par date d'ingestion sous `RAW_DIR/<source>/`.

Usage::

    # cœur métier
    python -m pipeline.feeder --source dvf --year 2024
    python -m pipeline.feeder --source social_housing
    python -m pipeline.feeder --source filosofi
    python -m pipeline.feeder --source arrondissements
    python -m pipeline.feeder --source air_quality

    # POI Paris OpenData
    python -m pipeline.feeder --source poi --poi-key velib_stations
    python -m pipeline.feeder --source poi --poi-key belib_bornes
    python -m pipeline.feeder --source poi --poi-key ecoles_elementaires
    # ...

    # POI data.gouv (musées, hôpitaux, monuments)
    python -m pipeline.feeder --source datagouv --datagouv-key musees_france
"""

from __future__ import annotations

import argparse
import sys

from .config import get_settings
from .logging_utils import get_logger, today_partition
from .sources import (
    air_quality,
    arrondissements,
    datagouv_poi,
    dvf,
    filosofi,
    paris_poi,
    social_housing,
)

CORE_SOURCES = {"dvf", "social_housing", "filosofi", "arrondissements", "air_quality"}
EXTRA_SOURCES = {"poi", "datagouv"}
SOURCES = CORE_SOURCES | EXTRA_SOURCES


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="feeder", description="Bronze ingestion (paramétrable).")
    p.add_argument("--source", required=True, choices=sorted(SOURCES))
    p.add_argument("--year", type=int, default=2024, help="Année DVF (défaut: 2024)")
    p.add_argument(
        "--ingestion-date",
        default=today_partition(),
        help="Date d'ingestion ISO YYYY-MM-DD (défaut: aujourd'hui UTC)",
    )
    p.add_argument(
        "--poi-key",
        default=None,
        help=f"Clef POI Paris OpenData parmi {sorted(paris_poi.POI_REGISTRY)}",
    )
    p.add_argument(
        "--datagouv-key",
        default=None,
        help=f"Clef data.gouv parmi {sorted(datagouv_poi.DATAGOUV_REGISTRY)}",
    )
    return p.parse_args(argv)


def run(
    source: str,
    year: int,
    ingestion_date: str,
    poi_key: str | None = None,
    datagouv_key: str | None = None,
) -> int:
    settings = get_settings()

    if source == "poi":
        if not poi_key:
            print("--poi-key is required when --source poi", file=sys.stderr)
            return 2
        sub = poi_key
    elif source == "datagouv":
        if not datagouv_key:
            print("--datagouv-key is required when --source datagouv", file=sys.stderr)
            return 2
        sub = datagouv_key
    else:
        sub = source

    logger = get_logger(f"feeder_{sub}")
    partition_dir = settings.partition_path(settings.raw_dir, sub, ingestion_date)
    logger.info("feeder · source=%s sub=%s · partition=%s", source, sub, partition_dir)

    try:
        if source == "dvf":
            dvf.fetch(
                year=year,
                raw_partition_dir=partition_dir,
                base_url=settings.dvf_base_url,
                logger=logger,
            )
        elif source == "social_housing":
            social_housing.fetch(
                raw_partition_dir=partition_dir,
                paris_opendata_base_url=settings.paris_opendata_base_url,
                logger=logger,
            )
        elif source == "filosofi":
            filosofi.fetch(
                raw_partition_dir=partition_dir,
                insee_url=settings.insee_filosofi_url,
                logger=logger,
            )
        elif source == "arrondissements":
            arrondissements.fetch(
                raw_partition_dir=partition_dir,
                geojson_url=settings.arrondissements_geojson_url,
                logger=logger,
            )
        elif source == "air_quality":
            air_quality.fetch(
                raw_partition_dir=partition_dir,
                airparif_url=settings.airparif_url,
                logger=logger,
            )
        elif source == "poi":
            paris_poi.fetch(
                poi_key=poi_key,  # type: ignore[arg-type]
                raw_partition_dir=partition_dir,
                paris_opendata_base_url=settings.paris_opendata_base_url,
                logger=logger,
            )
        elif source == "datagouv":
            datagouv_poi.fetch(
                key=datagouv_key,  # type: ignore[arg-type]
                raw_partition_dir=partition_dir,
                logger=logger,
            )
        else:
            logger.error("feeder · unknown source: %s", source)
            return 2
    except Exception as exc:
        logger.error("feeder · failed: %s", exc, exc_info=True)
        return 1

    logger.info("feeder · OK (source=%s sub=%s)", source, sub)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args.source, args.year, args.ingestion_date, args.poi_key, args.datagouv_key)


if __name__ == "__main__":
    sys.exit(main())
