"""Tests pour la normalisation des codes arrondissement et le parsing géo."""

from __future__ import annotations

import pytest
from etl.silver.processing import _normalize_code, _parse_geo_point


# ── _normalize_code ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    # Format 750xx direct
    ("75001", "75001"),
    ("75011", "75011"),
    ("75020", "75020"),
    # Format 751xx (code INSEE commune parisien)
    ("75101", "75001"),
    ("75120", "75020"),
    # Format numérique simple avec/sans suffixe
    ("1",    "75001"),
    ("20",   "75020"),
    ("1er",  "75001"),
    ("2e",   "75002"),
    ("15e",  "75015"),
    ("1ème", "75001"),
    # Cas limites
    ("75056", None),   # code INSEE de la commune entière
    (None,    None),
    ("",      None),
    ("75999", None),   # arrondissement hors plage
    ("21",    None),   # numéro hors plage
    ("0",     None),
])
def test_normalize_code(raw, expected):
    assert _normalize_code(raw) == expected


def test_normalize_code_int_input():
    """_normalize_code accepte les entiers en plus des chaînes."""
    assert _normalize_code(1) == "75001"
    assert _normalize_code(20) == "75020"


# ── _parse_geo_point ─────────────────────────────────────────────────────────

def test_parse_geo_point_paris():
    lat, lon = _parse_geo_point("48.8566, 2.3522")
    assert lat == pytest.approx(48.8566)
    assert lon == pytest.approx(2.3522)


def test_parse_geo_point_with_spaces():
    lat, lon = _parse_geo_point("  48.85 ,  2.35  ")
    assert lat == pytest.approx(48.85)
    assert lon == pytest.approx(2.35)


def test_parse_geo_point_none():
    assert _parse_geo_point(None) == (None, None)


def test_parse_geo_point_empty():
    assert _parse_geo_point("") == (None, None)


def test_parse_geo_point_single_value():
    assert _parse_geo_point("48.8566") == (None, None)


def test_parse_geo_point_non_numeric():
    assert _parse_geo_point("abc, def") == (None, None)


def test_parse_geo_point_out_of_france():
    """Coordonnées hors de la plage France (40-55°N, -5-10°E) rejetées."""
    assert _parse_geo_point("0.0, 0.0") == (None, None)
    assert _parse_geo_point("60.0, 2.3") == (None, None)
