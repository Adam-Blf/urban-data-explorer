"""Bronze layer - ingestion brute des sources Open Data.

Responsabilites :
- catalog.py  : catalogue des 82 sources (definitions, metadata, familles)
- scraper.py  : telechargement HTTP des fichiers CSV/GeoJSON
- io.py       : chargement CSV/TSV/GZ -> Silver DataFrame (Polars)
- external.py : sources enrichies DVF (prix immobilier) + INSEE Filosofi (revenus)
"""

from .catalog import ALL_SOURCES, FAMILIES, SOURCE_MAP, SourceSpec
from .scraper import download_dataset, scrape_catalog_metadata
from .io import load_source_as_silver
from .external import load_dvf_prices, load_filosofi_income

__all__ = [
    "ALL_SOURCES", "FAMILIES", "SOURCE_MAP", "SourceSpec",
    "download_dataset", "scrape_catalog_metadata",
    "load_source_as_silver",
    "load_dvf_prices", "load_filosofi_income",
]
