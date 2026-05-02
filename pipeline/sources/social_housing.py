"""Source · Logements sociaux financés à Paris (OpenData Paris).

Dataset · `logements-sociaux-finances` · pagination via `limit/offset`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
import polars as pl

DATASET_ID = "logements-sociaux-finances-a-paris"


def fetch(
    raw_partition_dir: Path,
    paris_opendata_base_url: str,
    logger: logging.Logger,
    page_size: int = 100,
    max_records: int = 50_000,
) -> Path:
    """Pagine l'API OpenData Paris jusqu'à épuisement et écrit un Parquet."""
    raw_partition_dir.mkdir(parents=True, exist_ok=True)
    url = f"{paris_opendata_base_url}/{DATASET_ID}/records"
    out = raw_partition_dir / "social_housing.parquet"

    rows: list[dict] = []
    offset = 0
    with httpx.Client(timeout=120.0) as client:
        while offset < max_records:
            params = {"limit": page_size, "offset": offset}
            logger.info("social_housing · GET offset=%d", offset)
            resp = client.get(url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            results = payload.get("results", [])
            if not results:
                break
            rows.extend(results)
            offset += len(results)
            if len(results) < page_size:
                break

    if not rows:
        logger.error("social_housing · empty response from OpenData Paris")
        df = pl.DataFrame()
    else:
        df = pl.from_dicts(rows, infer_schema_length=2_000)

    df.write_parquet(out, compression="snappy")
    logger.info("social_housing · wrote %s (%d rows)", out, df.height)
    return out
