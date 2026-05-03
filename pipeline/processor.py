"""Processor · Silver layer.

Lecture depuis `RAW_DIR/<source>/year=.../...`, nettoyage, validation
(au moins 5 règles), jointure spatiale arrondissement, agrégations,
window functions, écriture vers `SILVER_DIR/<source>/year=.../...`.

Usage::

    python -m pipeline.processor --source dvf
    python -m pipeline.processor --source social_housing
    python -m pipeline.processor --source filosofi
    python -m pipeline.processor --source arrondissements
    python -m pipeline.processor --source air_quality
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import polars as pl
from shapely.geometry import Point, shape

from .config import get_settings
from .logging_utils import get_logger, today_partition
from .sources import datagouv_poi, paris_poi
from .sources.poi_silver import normalize as poi_normalize

SOURCES = {
    "dvf",
    "social_housing",
    "filosofi",
    "arrondissements",
    "air_quality",
    "poi",
}


# ---------------------------------------------------------------------------
# Helpers · jointure spatiale arrondissement
# ---------------------------------------------------------------------------

def _load_arrondissement_polygons(geojson_path: Path) -> list[tuple[str, object]]:
    """Charge les polygones arrondissement, retourne `[(code, shape), ...]`."""
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    out: list[tuple[str, object]] = []
    for feat in payload.get("features", []):
        props = feat.get("properties", {})
        code = (
            props.get("code_arrondissement")
            or props.get("c_arinsee")
            or _normalize_arr_code(props.get("c_ar"))
        )
        if code is None:
            continue
        out.append((str(code), shape(feat["geometry"])))
    return out


def _normalize_arr_code(c_ar) -> str | None:
    if c_ar is None:
        return None
    try:
        return f"751{int(c_ar):02d}"
    except (TypeError, ValueError):
        return None


def _spatial_join_arrondissement(
    df: pl.DataFrame,
    polygons: list[tuple[str, object]],
    lon_col: str,
    lat_col: str,
) -> pl.DataFrame:
    """Ajoute une colonne `code_arrondissement` via point-in-polygon."""
    lons = df[lon_col].to_list()
    lats = df[lat_col].to_list()
    codes: list[str | None] = []
    for lon, lat in zip(lons, lats, strict=False):
        if lon is None or lat is None:
            codes.append(None)
            continue
        pt = Point(lon, lat)
        match = next((c for c, poly in polygons if poly.contains(pt)), None)
        codes.append(match)
    return df.with_columns(pl.Series("code_arrondissement", codes, dtype=pl.Utf8))


# ---------------------------------------------------------------------------
# Validators · au moins 5 règles partagées
# ---------------------------------------------------------------------------

def apply_validation_rules(df: pl.DataFrame, rules: dict[str, pl.Expr], logger) -> pl.DataFrame:
    """Applique chaque règle, log le rejet, garde les lignes valides."""
    valid = df
    for name, predicate in rules.items():
        before = valid.height
        valid = valid.filter(predicate)
        rejected = before - valid.height
        if rejected > 0:
            logger.info("validation · rule=%s rejected=%d kept=%d", name, rejected, valid.height)
    return valid


# ---------------------------------------------------------------------------
# Per-source silver
# ---------------------------------------------------------------------------

def _silver_dvf(raw_root: Path, polygons, logger) -> pl.DataFrame:
    files = sorted(raw_root.rglob("dvf_paris_*.parquet"))
    if not files:
        raise FileNotFoundError(f"no DVF parquet under {raw_root}")
    logger.info("dvf · reading %d parquet partitions", len(files))
    df = pl.concat([pl.read_parquet(f) for f in files])

    df = df.with_columns([
        pl.col("date_mutation").str.to_date(format="%Y-%m-%d", strict=False),
        pl.col("valeur_fonciere").cast(pl.Float64, strict=False),
        pl.col("surface_reelle_bati").cast(pl.Float64, strict=False),
        pl.col("longitude").cast(pl.Float64, strict=False),
        pl.col("latitude").cast(pl.Float64, strict=False),
        pl.col("nombre_pieces_principales").cast(pl.Int64, strict=False),
    ])

    rules = {
        "non_null_date":      pl.col("date_mutation").is_not_null(),
        "non_null_valeur":    pl.col("valeur_fonciere").is_not_null() & (pl.col("valeur_fonciere") > 0),
        "non_null_surface":   pl.col("surface_reelle_bati").is_not_null() & (pl.col("surface_reelle_bati") > 9),
        "valeur_realistic":   pl.col("valeur_fonciere").is_between(50_000, 50_000_000),
        "geo_within_paris":   pl.col("longitude").is_between(2.20, 2.50)
                              & pl.col("latitude").is_between(48.80, 48.92),
        "type_local_logement": pl.col("type_local").is_in(["Appartement", "Maison"]),
    }
    df = apply_validation_rules(df, rules, logger)

    df = df.with_columns(
        (pl.col("valeur_fonciere") / pl.col("surface_reelle_bati")).alias("prix_m2")
    )

    df = _spatial_join_arrondissement(df, polygons, "longitude", "latitude")
    df = df.filter(pl.col("code_arrondissement").is_not_null())

    df = df.cache()  # ⇒ persist en RAM, visible Spark UI dans la version Spark
    logger.info("dvf · cached silver dataframe in memory")

    df = df.with_columns([
        pl.col("date_mutation").dt.year().alias("year"),
        pl.col("date_mutation").dt.month().alias("month"),
    ])

    df = df.with_columns([
        pl.col("prix_m2")
            .median()
            .over("code_arrondissement")
            .alias("prix_m2_median_arr"),
        pl.col("prix_m2")
            .rank(method="dense", descending=True)
            .over(["year", "month"])
            .alias("rank_prix_m2_dans_mois"),
        (pl.col("prix_m2") - pl.col("prix_m2")
            .shift(1)
            .over(["code_arrondissement", "year"]))
            .alias("delta_prix_m2_vs_prev"),
    ])

    return df


def _silver_social_housing(raw_root: Path, logger) -> pl.DataFrame:
    files = sorted(raw_root.rglob("social_housing.parquet"))
    if not files:
        raise FileNotFoundError(f"no social_housing parquet under {raw_root}")
    df = pl.read_parquet(files[-1])

    arr_col = next((c for c in df.columns if "arrond" in c.lower()), None)
    nb_col = next(
        (c for c in df.columns if "nombre" in c.lower() or "logements" in c.lower()),
        None,
    )
    year_col = next((c for c in df.columns if c.lower() in {"annee", "year"}), None)

    if arr_col is None or nb_col is None or year_col is None:
        logger.error("social_housing · unexpected schema · cols=%s", df.columns)
        return df

    df = df.with_columns([
        pl.col(arr_col).cast(pl.Utf8).str.extract(r"(\d+)").alias("arr_num"),
        pl.col(nb_col).cast(pl.Int64, strict=False).alias("nb_logements"),
        pl.col(year_col).cast(pl.Int64, strict=False).alias("year"),
    ]).filter(
        pl.col("arr_num").is_not_null()
        & pl.col("nb_logements").is_not_null()
        & (pl.col("nb_logements") > 0)
    )

    df = df.with_columns(
        pl.format("751{}", pl.col("arr_num").str.zfill(2)).alias("code_arrondissement")
    )

    df = df.group_by(["code_arrondissement", "year"]).agg(
        pl.col("nb_logements").sum().alias("nb_logements_finances"),
    )
    return df


def _silver_filosofi(raw_root: Path, logger) -> pl.DataFrame:
    files = sorted(raw_root.rglob("filosofi_paris.parquet"))
    if not files:
        raise FileNotFoundError(f"no filosofi parquet under {raw_root}")
    df = pl.read_parquet(files[-1])
    keep = [c for c in df.columns if c.startswith("MED") or c.startswith("PIMP") or c == "code_arrondissement"]
    return df.select(keep)


def _silver_arrondissements(raw_root: Path, logger) -> pl.DataFrame:
    files = sorted(raw_root.rglob("arrondissements.geojson"))
    if not files:
        raise FileNotFoundError(f"no arrondissements geojson under {raw_root}")
    payload = json.loads(files[-1].read_text(encoding="utf-8"))
    rows = []
    for feat in payload["features"]:
        props = feat.get("properties", {})
        geom = shape(feat["geometry"])
        code = (
            props.get("code_arrondissement")
            or _normalize_arr_code(props.get("c_ar"))
        )
        rows.append({
            "code_arrondissement": code,
            "centroid_lon": geom.centroid.x,
            "centroid_lat": geom.centroid.y,
            "area_km2": geom.area * 111 * 111,
            "label": props.get("l_ar") or f"{int(str(code)[-2:])}e",
        })
    return pl.from_dicts(rows)


def _silver_air_quality(raw_root: Path, logger) -> pl.DataFrame:
    files = sorted(raw_root.rglob("air_quality.parquet"))
    if not files:
        raise FileNotFoundError(f"no air_quality parquet under {raw_root}")
    df = pl.read_parquet(files[-1])
    pollutants = [c for c in df.columns if c.lower() in {"no2", "o3", "pm10", "pm25"}]
    if not pollutants:
        logger.error("air_quality · no pollutant column found · cols=%s", df.columns)
        return df
    df = df.with_columns([pl.col(p).cast(pl.Float64, strict=False) for p in pollutants])
    df = df.with_columns([
        pl.fold(
            acc=pl.lit(0.0),
            function=lambda acc, x: acc + x.fill_null(0),
            exprs=[pl.col(p) for p in pollutants],
        ).alias("aqi_sum"),
    ])
    df = df.with_columns(
        (pl.col("aqi_sum") / len(pollutants)).alias("aqi_mean_paris")
    )
    return df


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _silver_poi(settings, polygons, logger, ingestion_date) -> pl.DataFrame:
    """Concatène TOUS les POI bruts (Paris + data.gouv) en un silver unifié."""
    frames: list[pl.DataFrame] = []

    for key in paris_poi.POI_REGISTRY:
        files = sorted((settings.raw_dir / key).rglob(f"{key}.parquet"))
        if not files:
            logger.info("poi · skip %s · no raw parquet found", key)
            continue
        frames.append(poi_normalize(files[-1], polygons, logger, ingestion_date))

    for key in datagouv_poi.DATAGOUV_REGISTRY:
        files = sorted((settings.raw_dir / key).rglob(f"{key}.parquet"))
        if not files:
            logger.info("poi · skip %s · no raw parquet found", key)
            continue
        frames.append(poi_normalize(files[-1], polygons, logger, ingestion_date))

    if not frames:
        logger.error("poi · no source ingested · run feeder with --source poi/datagouv first")
        return pl.DataFrame({
            "code_arrondissement": pl.Series([], dtype=pl.Utf8),
            "category":            pl.Series([], dtype=pl.Utf8),
            "subcategory":         pl.Series([], dtype=pl.Utf8),
            "name":                pl.Series([], dtype=pl.Utf8),
            "lon":                 pl.Series([], dtype=pl.Float64),
            "lat":                 pl.Series([], dtype=pl.Float64),
            "ingestion_date":      pl.Series([], dtype=pl.Utf8),
        })

    df = pl.concat(frames, how="vertical_relaxed")
    df = df.cache()
    logger.info("poi · concatenated %d frames · %d rows total", len(frames), df.height)
    return df


def run(source: str, ingestion_date: str) -> int:
    settings = get_settings()
    logger = get_logger(f"processor_{source}")

    raw_root = settings.raw_dir / source
    silver_partition = settings.partition_path(settings.silver_dir, source, ingestion_date)
    silver_partition.mkdir(parents=True, exist_ok=True)
    out = silver_partition / f"{source}.parquet"

    polygons: list = []
    if source in {"dvf", "poi"}:
        arr_files = sorted((settings.raw_dir / "arrondissements").rglob("arrondissements.geojson"))
        if not arr_files:
            logger.error(
                "%s · arrondissements geojson missing · run feeder for arrondissements first",
                source,
            )
            return 3
        polygons = _load_arrondissement_polygons(arr_files[-1])

    try:
        if source == "dvf":
            df = _silver_dvf(raw_root, polygons, logger)
        elif source == "social_housing":
            df = _silver_social_housing(raw_root, logger)
        elif source == "filosofi":
            df = _silver_filosofi(raw_root, logger)
        elif source == "arrondissements":
            df = _silver_arrondissements(raw_root, logger)
        elif source == "air_quality":
            df = _silver_air_quality(raw_root, logger)
        elif source == "poi":
            df = _silver_poi(settings, polygons, logger, ingestion_date)
        else:
            logger.error("processor · unknown source: %s", source)
            return 2
    except Exception as exc:
        logger.error("processor · failed: %s", exc, exc_info=True)
        return 1

    df.write_parquet(out, compression="snappy")
    logger.info("processor · wrote silver %s (%d rows, %d cols)", out, df.height, df.width)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="processor", description="Silver layer (paramétrable).")
    p.add_argument("--source", required=True, choices=sorted(SOURCES))
    p.add_argument("--ingestion-date", default=today_partition())
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args.source, args.ingestion_date)


if __name__ == "__main__":
    sys.exit(main())
