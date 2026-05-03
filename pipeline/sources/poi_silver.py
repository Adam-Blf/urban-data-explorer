"""Silver POI · normalise n'importe quel dataset POI vers un schéma commun.

Schéma de sortie ·

    code_arrondissement  string
    category             string  (transport, sante, ...)
    subcategory          string  (velib, hopital, ...)
    name                 string?
    lon                  float64
    lat                  float64
    ingestion_date       date

Détecte automatiquement les colonnes lon/lat (geo_point_2d, geo_shape, lon/lat,
longitude/latitude, X/Y...) qui varient d'un dataset OpenData à l'autre.
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
from shapely.geometry import Point


def _extract_lon_lat(df: pl.DataFrame, logger: logging.Logger) -> pl.DataFrame:
    """Tente d'extraire (lon, lat) à partir des colonnes communes OpenData."""
    cols = {c.lower(): c for c in df.columns}

    # 1) lon/lat plats
    for lon_alias, lat_alias in [
        ("longitude", "latitude"),
        ("lon", "lat"),
        ("x_long", "y_lat"),
        ("x", "y"),
    ]:
        if lon_alias in cols and lat_alias in cols:
            return df.with_columns([
                pl.col(cols[lon_alias]).cast(pl.Float64, strict=False).alias("lon"),
                pl.col(cols[lat_alias]).cast(pl.Float64, strict=False).alias("lat"),
            ])

    # 2) geo_point_2d format dict {"lat": ..., "lon": ...}
    if "geo_point_2d" in cols:
        col = cols["geo_point_2d"]
        sample = df[col].drop_nulls().head(1)
        if sample.height > 0 and isinstance(sample[0], dict):
            return df.with_columns([
                pl.col(col).struct.field("lon").alias("lon"),
                pl.col(col).struct.field("lat").alias("lat"),
            ])
        # Sometimes string "lat,lon"
        return df.with_columns([
            pl.col(col).cast(pl.Utf8).str.split(",").list.get(1)
                .cast(pl.Float64, strict=False).alias("lon"),
            pl.col(col).cast(pl.Utf8).str.split(",").list.get(0)
                .cast(pl.Float64, strict=False).alias("lat"),
        ])

    # 3) geo_shape (point) → coordinates[0], [1]
    if "geo_shape" in cols:
        col = cols["geo_shape"]
        return df.with_columns([
            pl.col(col).struct.field("geometry").struct.field("coordinates")
                .list.get(0).cast(pl.Float64, strict=False).alias("lon"),
            pl.col(col).struct.field("geometry").struct.field("coordinates")
                .list.get(1).cast(pl.Float64, strict=False).alias("lat"),
        ])

    logger.error("poi_silver · no geo column detected · cols=%s", df.columns)
    return df.with_columns([
        pl.lit(None, dtype=pl.Float64).alias("lon"),
        pl.lit(None, dtype=pl.Float64).alias("lat"),
    ])


def _spatial_join(
    df: pl.DataFrame,
    polygons: list[tuple[str, object]],
) -> pl.DataFrame:
    lons = df["lon"].to_list()
    lats = df["lat"].to_list()
    codes: list[str | None] = []
    for lon, lat in zip(lons, lats, strict=False):
        if lon is None or lat is None:
            codes.append(None)
            continue
        pt = Point(lon, lat)
        codes.append(next((c for c, poly in polygons if poly.contains(pt)), None))
    return df.with_columns(pl.Series("code_arrondissement", codes, dtype=pl.Utf8))


def normalize(
    raw_parquet: Path,
    polygons: list[tuple[str, object]],
    logger: logging.Logger,
    ingestion_date: str,
) -> pl.DataFrame:
    """Charge un parquet POI brut et retourne un DataFrame normalisé."""
    df = pl.read_parquet(raw_parquet)
    if df.height == 0:
        return pl.DataFrame({
            "code_arrondissement": pl.Series([], dtype=pl.Utf8),
            "category":            pl.Series([], dtype=pl.Utf8),
            "subcategory":         pl.Series([], dtype=pl.Utf8),
            "name":                pl.Series([], dtype=pl.Utf8),
            "lon":                 pl.Series([], dtype=pl.Float64),
            "lat":                 pl.Series([], dtype=pl.Float64),
            "ingestion_date":      pl.Series([], dtype=pl.Utf8),
        })

    df = _extract_lon_lat(df, logger)
    df = df.filter(pl.col("lon").is_not_null() & pl.col("lat").is_not_null())
    df = df.filter(
        pl.col("lon").is_between(2.20, 2.50)
        & pl.col("lat").is_between(48.80, 48.92)
    )
    df = _spatial_join(df, polygons)
    df = df.filter(pl.col("code_arrondissement").is_not_null())

    name_col = next(
        (c for c in df.columns if c.lower() in {"name", "nom", "libelle", "title", "stationname"}),
        None,
    )
    if name_col is None:
        df = df.with_columns(pl.lit(None, dtype=pl.Utf8).alias("name"))
    else:
        df = df.with_columns(pl.col(name_col).cast(pl.Utf8).alias("name"))

    if "category" not in df.columns:
        df = df.with_columns(pl.lit("unknown").alias("category"))
    if "subcategory" not in df.columns:
        df = df.with_columns(pl.lit("unknown").alias("subcategory"))

    df = df.with_columns(pl.lit(ingestion_date).alias("ingestion_date"))
    return df.select([
        "code_arrondissement",
        "category",
        "subcategory",
        "name",
        "lon",
        "lat",
        "ingestion_date",
    ])
