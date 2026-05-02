"""Orchestrateur · enchaîne feeder → processor → datamart pour toutes les sources.

Usage::

    python -m pipeline.run_pipeline --layers all
    python -m pipeline.run_pipeline --layers feeder
    python -m pipeline.run_pipeline --layers processor
    python -m pipeline.run_pipeline --layers datamart
    python -m pipeline.run_pipeline --skip-poi      # cœur métier seulement
"""

from __future__ import annotations

import argparse
import sys

from . import datamart, feeder, processor
from .logging_utils import get_logger, today_partition
from .sources import datagouv_poi, paris_poi

CORE_SOURCES = ["arrondissements", "filosofi", "social_housing", "air_quality", "dvf"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="run_pipeline")
    p.add_argument("--layers", default="all", choices=["all", "feeder", "processor", "datamart"])
    p.add_argument("--year", type=int, default=2024)
    p.add_argument("--ingestion-date", default=today_partition())
    p.add_argument("--skip-poi", action="store_true",
                   help="Ignore les POI (Vélib, écoles, musées, hôpitaux, ...)")
    return p.parse_args(argv)


def run(layers: str, year: int, ingestion_date: str, skip_poi: bool = False) -> int:
    log = get_logger("orchestrator")

    if layers in {"all", "feeder"}:
        for src in CORE_SOURCES:
            log.info("orchestrator · feeder · %s", src)
            rc = feeder.run(src, year, ingestion_date)
            if rc != 0:
                log.error("orchestrator · feeder %s failed (rc=%d) · continuing", src, rc)

        if not skip_poi:
            for poi_key in paris_poi.POI_REGISTRY:
                log.info("orchestrator · feeder · poi=%s", poi_key)
                rc = feeder.run("poi", year, ingestion_date, poi_key=poi_key)
                if rc != 0:
                    log.error("orchestrator · feeder poi/%s failed · continuing", poi_key)

            for dg_key in datagouv_poi.DATAGOUV_REGISTRY:
                log.info("orchestrator · feeder · datagouv=%s", dg_key)
                rc = feeder.run("datagouv", year, ingestion_date, datagouv_key=dg_key)
                if rc != 0:
                    log.error("orchestrator · feeder datagouv/%s failed · continuing", dg_key)

    if layers in {"all", "processor"}:
        for src in CORE_SOURCES:
            log.info("orchestrator · processor · %s", src)
            rc = processor.run(src, ingestion_date)
            if rc != 0:
                log.error("orchestrator · processor %s failed (rc=%d) · continuing", src, rc)

        if not skip_poi:
            log.info("orchestrator · processor · poi (concat all sources)")
            rc = processor.run("poi", ingestion_date)
            if rc != 0:
                log.error("orchestrator · processor poi failed · continuing")

    if layers in {"all", "datamart"}:
        log.info("orchestrator · datamart · build=all")
        rc = datamart.run("all")
        if rc != 0:
            return rc

    log.info("orchestrator · pipeline OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args.layers, args.year, args.ingestion_date, args.skip_poi)


if __name__ == "__main__":
    sys.exit(main())
