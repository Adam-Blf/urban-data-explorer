"""Tests pour les fonctions de construction Silver/Gold (Polars)."""

from __future__ import annotations

import pytest
import polars as pl
from etl.processing import (
    build_gold_dashboard,
    build_gold_timeline,
    _family_counts,
    build_silver_record,
)
from etl.catalog import SOURCE_MAP


# ── Helpers ──────────────────────────────────────────────────────────────────

def _silver_frame(n_per_arr: int = 3, family: str = "green_space") -> pl.DataFrame:
    """Crée un Silver DataFrame synthétique (sans accès réseau ni FS)."""
    rows = []
    for i in range(1, 21):
        code = f"750{i:02d}"
        for _ in range(n_per_arr):
            rows.append({
                "source_id": "espaces_verts",
                "family": family,
                "arrondissement_code": code,
                "latitude": 48.85 + i * 0.001,
                "longitude": 2.35 + i * 0.001,
                "code_iris": None,
                "nom_iris": None,
                "address": None,
                "quality_flag": "code_only",
            })
    return pl.DataFrame(rows)


# ── _family_counts ────────────────────────────────────────────────────────────

def test_family_counts_basic():
    df = _silver_frame(3)
    counts = _family_counts(df)
    assert len(counts) == 20
    for code, fams in counts.items():
        assert fams["green_space"] == 3


def test_family_counts_empty_frame():
    empty = pl.DataFrame(schema={
        "arrondissement_code": pl.Utf8,
        "family": pl.Utf8,
    })
    assert _family_counts(empty) == {}


def test_family_counts_null_codes_excluded():
    df = pl.DataFrame({
        "source_id": ["s1", "s2"],
        "family": ["green_space", "mobility"],
        "arrondissement_code": [None, "75011"],
        "latitude": [48.85, 48.86],
        "longitude": [2.35, 2.36],
        "code_iris": [None, None],
        "nom_iris": [None, None],
        "address": [None, None],
        "quality_flag": ["code_only", "code_only"],
    })
    counts = _family_counts(df)
    assert "75011" in counts
    assert None not in counts


# ── build_gold_dashboard ──────────────────────────────────────────────────────

def test_build_gold_dashboard_shape():
    df = _silver_frame(3)
    gold = build_gold_dashboard(df)
    assert not gold.is_empty()
    assert gold.height == 20
    assert "arrondissement_code" in gold.columns
    assert "prix_m2" in gold.columns
    assert "m2_abordables" in gold.columns
    assert "accessibilite_idx" in gold.columns
    assert "data_source" in gold.columns


def test_build_gold_dashboard_values_in_range():
    df = _silver_frame(2)
    gold = build_gold_dashboard(df)
    for row in gold.to_dicts():
        assert 0 <= row["score"] <= 100, f"score hors plage pour {row['arrondissement_code']}"
        assert row["prix_m2"] > 0
        assert row["revenu_median"] > 0
        assert row["m2_abordables"] >= 0
        assert 0 <= row["accessibilite_idx"] <= 100


def test_build_gold_dashboard_data_source_is_reference():
    """Sans DVF/Filosofi disponibles, data_source doit être 'reference'."""
    df = _silver_frame(2)
    gold = build_gold_dashboard(df)
    sources = gold.get_column("data_source").to_list()
    # En l'absence de fichiers DVF/Filosofi, toutes les lignes sont 'reference'
    assert all(s in ("reference", "real") for s in sources)


def test_build_gold_dashboard_empty_input():
    empty = pl.DataFrame(schema={
        "source_id": pl.Utf8,
        "family": pl.Utf8,
        "arrondissement_code": pl.Utf8,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "code_iris": pl.Utf8,
        "nom_iris": pl.Utf8,
        "address": pl.Utf8,
        "quality_flag": pl.Utf8,
    })
    result = build_gold_dashboard(empty)
    assert result.is_empty()


# ── build_gold_timeline ───────────────────────────────────────────────────────

def test_build_gold_timeline_shape():
    df = _silver_frame(3)
    tl = build_gold_timeline(df)
    assert not tl.is_empty()
    # 20 arrondissements × 12 mois = 240 lignes
    assert tl.height == 240
    assert "environnement_idx" in tl.columns


def test_build_gold_timeline_months_coverage():
    df = _silver_frame(2)
    tl = build_gold_timeline(df)
    months = tl.get_column("month").unique().sort().to_list()
    assert len(months) == 12


def test_build_gold_timeline_empty_input():
    empty = pl.DataFrame(schema={
        "source_id": pl.Utf8,
        "family": pl.Utf8,
        "arrondissement_code": pl.Utf8,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "code_iris": pl.Utf8,
        "nom_iris": pl.Utf8,
        "address": pl.Utf8,
        "quality_flag": pl.Utf8,
    })
    assert build_gold_timeline(empty).is_empty()


# ── build_silver_record ───────────────────────────────────────────────────────

def test_silver_record_with_code():
    spec = SOURCE_MAP["espaces_verts"]
    row = {"adresse_codepostal": "75011"}
    rec = build_silver_record(row, spec)
    assert rec["source_id"] == "espaces_verts"
    assert rec["family"] == "green_space"
    assert rec["arrondissement_code"] == "75011"


def test_silver_record_unknown_code():
    spec = SOURCE_MAP["espaces_verts"]
    row = {"adresse_codepostal": "99999"}
    rec = build_silver_record(row, spec)
    assert rec["arrondissement_code"] is None
