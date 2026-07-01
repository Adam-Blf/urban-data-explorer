"""ETL – Pipeline de donnees Open Data Paris (architecture medaillon).

Structure par couche :
  etl/bronze/  - ingestion brute (catalogue 82 sources, scraping, chargement CSV)
  etl/silver/  - normalisation, geocodage IRIS, qualite des donnees
  etl/gold/    - datamarts agreges, metriques pipeline

Retrocompatibilite : les imports etl.catalog / etl.processing / etc. fonctionnent
via les sous-modules directement (Python resout etl.bronze.catalog automatiquement).
"""

from .bronze.catalog import ALL_SOURCES, FAMILIES, SOURCE_MAP, SourceSpec
from .bronze.io import load_source_as_silver
from .bronze.scraper import download_dataset
from .bronze.external import load_dvf_prices, load_filosofi_income
from .silver.processing import (
    build_silver_record,
    build_gold_dashboard,
    build_gold_timeline,
    resolve_iris,
)
from .silver.quality import compute_quality
from .gold.metrics import record_stage, load_metrics

__all__ = [
    "ALL_SOURCES", "FAMILIES", "SOURCE_MAP", "SourceSpec",
    "load_source_as_silver", "download_dataset",
    "load_dvf_prices", "load_filosofi_income",
    "build_silver_record", "build_gold_dashboard", "build_gold_timeline",
    "resolve_iris", "compute_quality",
    "record_stage", "load_metrics",
]
