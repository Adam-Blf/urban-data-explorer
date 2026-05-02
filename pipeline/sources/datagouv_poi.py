"""Source · POI nationaux issus de data.gouv (musées, hôpitaux, monuments).

Ces datasets exposent CSV bruts. On télécharge, on filtre Paris/IDF si possible,
on persiste en Parquet.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path

import httpx
import polars as pl


@dataclass(frozen=True)
class DataGouvSource:
    csv_url: str
    category: str
    subcategory: str
    filter_paris_col: str | None = None  # nom de la colonne dept (ex "DEP")
    paris_value: str = "75"


DATAGOUV_REGISTRY: dict[str, DataGouvSource] = {
    "musees_france": DataGouvSource(
        # snapshot CSV stable du jeu Musées de France
        csv_url="https://www.data.gouv.fr/api/1/datasets/r/4f0bf161-d9c2-4f8f-b305-5ce82b87b3a3",
        category="culture",
        subcategory="musee",
        filter_paris_col="REGION",
        paris_value="11",  # Île-de-France
    ),
    "hopitaux_idf": DataGouvSource(
        csv_url="https://www.data.gouv.fr/api/1/datasets/r/82b16f07-f1d6-4ac7-9d8a-9f4cb5b0a5ad",
        category="sante",
        subcategory="hopital",
    ),
    "monuments_historiques": DataGouvSource(
        csv_url="https://www.data.gouv.fr/api/1/datasets/r/a2b18a76-ba2f-4127-9446-4e2fda5c812a",
        category="culture",
        subcategory="monument",
    ),
}


def fetch(
    key: str,
    raw_partition_dir: Path,
    logger: logging.Logger,
) -> Path:
    if key not in DATAGOUV_REGISTRY:
        raise KeyError(f"unknown datagouv key: {key}")
    src = DATAGOUV_REGISTRY[key]
    raw_partition_dir.mkdir(parents=True, exist_ok=True)
    out = raw_partition_dir / f"{key}.parquet"

    logger.info("%s · downloading %s", key, src.csv_url)
    try:
        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            resp = client.get(src.csv_url)
            resp.raise_for_status()
            df = pl.read_csv(
                io.BytesIO(resp.content),
                separator=";",
                infer_schema_length=10_000,
                ignore_errors=True,
                null_values=["", "NA", "ND"],
                encoding="utf8-lossy",
            )
    except (httpx.HTTPError, pl.exceptions.PolarsError) as e:
        logger.error("%s · fetch failed (%s) · empty parquet", key, e)
        df = pl.DataFrame()

    if (
        src.filter_paris_col
        and src.filter_paris_col in df.columns
        and df.height > 0
    ):
        before = df.height
        df = df.filter(
            pl.col(src.filter_paris_col).cast(pl.Utf8) == src.paris_value
        )
        logger.info("%s · filtered Paris/IDF: %d → %d", key, before, df.height)

    if df.height > 0:
        df = df.with_columns([
            pl.lit(src.category).alias("category"),
            pl.lit(src.subcategory).alias("subcategory"),
        ])

    df.write_parquet(out, compression="snappy")
    logger.info("%s · wrote %s (%d rows)", key, out, df.height)
    return out
