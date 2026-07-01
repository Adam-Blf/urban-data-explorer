"""Silver layer - normalisation, geocodage, construction des datamarts.

Responsabilites :
- processing.py : Bronze -> Silver (normalisation codes, geocodage IRIS)
                  Silver -> Gold (build_gold_dashboard, build_gold_timeline)
- quality.py    : rapport qualite des donnees (completude, fraicheur, out-of-range)
"""

from .processing import (
    build_silver_record,
    build_gold_dashboard,
    build_gold_timeline,
    resolve_iris,
    reverse_geocode_api,
)
from .quality import compute_quality

__all__ = [
    "build_silver_record",
    "build_gold_dashboard",
    "build_gold_timeline",
    "resolve_iris",
    "reverse_geocode_api",
    "compute_quality",
]
