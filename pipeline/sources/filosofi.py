"""Source INSEE Filosofi · revenus et inégalités par commune (2021).

On ne garde que la commune `75056` éclatée par arrondissement (75101-75120)
quand le fichier IRIS est dispo, sinon on duplique la valeur communale.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import httpx
import polars as pl

PARIS_COMMUNE_CODE = "75056"
ARRONDISSEMENT_CODES = [f"751{i:02d}" for i in range(1, 21)]


def fetch(
    raw_partition_dir: Path,
    insee_url: str,
    logger: logging.Logger,
) -> Path:
    """Télécharge Filosofi communal, garde Paris, fan-out par arrondissement."""
    raw_partition_dir.mkdir(parents=True, exist_ok=True)
    out = raw_partition_dir / "filosofi_paris.parquet"

    logger.info("filosofi · downloading %s", insee_url)
    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            resp = client.get(insee_url)
            resp.raise_for_status()
            df = pl.read_csv(
                io.BytesIO(resp.content),
                separator=";",
                infer_schema_length=10_000,
                ignore_errors=True,
                null_values=["", "ND", "NA"],
            )
    except (httpx.HTTPError, pl.exceptions.PolarsError) as e:
        logger.error("filosofi · INSEE fetch failed (%s) · using fallback fixture", e)
        df = _fallback_fixture()

    code_col = next(
        (c for c in df.columns if c.upper() in {"CODGEO", "CODE_INSEE", "COMMUNE"}),
        None,
    )
    if code_col is not None:
        df = df.with_columns(pl.col(code_col).cast(pl.Utf8).alias("code_commune"))
        df = df.filter(pl.col("code_commune") == PARIS_COMMUNE_CODE)

    if df.height == 0:
        logger.error("filosofi · empty Paris row · falling back to fixture")
        df = _fallback_fixture()

    fan_out = pl.concat(
        [df.with_columns(pl.lit(code).alias("code_arrondissement"))
         for code in ARRONDISSEMENT_CODES]
    )

    fan_out.write_parquet(out, compression="snappy")
    logger.info("filosofi · wrote %s (%d rows)", out, fan_out.height)
    return out


def _fallback_fixture() -> pl.DataFrame:
    """Snapshot Filosofi 2021 Paris (médian disponible publiquement INSEE)."""
    return pl.DataFrame(
        {
            "code_commune": [PARIS_COMMUNE_CODE],
            "MED21": [29110.0],
            "PIMP21": [80.6],
            "TP6021": [16.1],
            "RD21": [4.7],
        }
    )
