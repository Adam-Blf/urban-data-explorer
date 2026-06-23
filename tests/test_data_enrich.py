"""Tests de régression pour _enrich_district_row (fix #4).

Vérifie que les valeurs réelles du parquet Gold ne sont pas écrasées
par les constantes de référence codées en dur.
"""

from __future__ import annotations

import pytest
from api.data import _enrich_district_row, PRIX_M2_BASES, REVENU_MEDIAN_BASES


# ── Helpers ──────────────────────────────────────────────────────────────────

def _base_raw_row(code: str = "75011") -> dict:
    """raw_row minimal sans valeurs réelles (simule le path math generator)."""
    return {
        "name": "Popincourt",
        "label": "11e",
        "x": 425,
        "y": 180,
        "environnement_count": 3,
        "mobilite_count": 7,
        "vie_quotidienne_count": 14,
        "logement_urbanisme_count": 6,
        "accessibility_index": 65.0,
        "pressure_index": 28.0,
        "attractiveness_index": 55.0,
    }


# ── Fallback vers les constantes ──────────────────────────────────────────────

def test_fallback_uses_prix_m2_constant():
    """Sans prix_m2 dans raw_row, utilise la constante de référence."""
    code = "75011"
    row = _enrich_district_row(code, _base_raw_row(code))
    assert row["prix_m2"] == pytest.approx(PRIX_M2_BASES[code])
    assert row["data_source"] == "reference"


def test_fallback_uses_revenu_median_constant():
    code = "75006"
    row = _enrich_district_row(code, _base_raw_row(code))
    assert row["revenu_median"] == pytest.approx(REVENU_MEDIAN_BASES[code])


# ── Fix #4 : les vraies valeurs sont préservées ───────────────────────────────

def test_real_prix_m2_is_preserved():
    """Fix #4 : un prix_m2 réel dans raw_row ne doit PAS être écrasé."""
    code = "75011"
    raw = _base_raw_row(code)
    raw["prix_m2"] = 12_345.0
    row = _enrich_district_row(code, raw)
    assert row["prix_m2"] == pytest.approx(12_345.0)
    # La constante de référence ne doit PAS être utilisée
    assert row["prix_m2"] != pytest.approx(PRIX_M2_BASES[code])


def test_real_revenu_median_is_preserved():
    code = "75018"
    raw = _base_raw_row(code)
    raw["revenu_median"] = 42_000.0
    row = _enrich_district_row(code, raw)
    assert row["revenu_median"] == pytest.approx(42_000.0)
    assert row["revenu_median"] != pytest.approx(REVENU_MEDIAN_BASES[code])


def test_real_sales_volume_is_preserved():
    code = "75001"
    raw = _base_raw_row(code)
    raw["sales_volume"] = 999
    row = _enrich_district_row(code, raw)
    assert row["sales_volume"] == 999


def test_data_source_real_is_propagated():
    code = "75008"
    raw = _base_raw_row(code)
    raw["prix_m2"] = 14_500.0
    raw["data_source"] = "real"
    row = _enrich_district_row(code, raw)
    assert row["data_source"] == "real"


def test_zero_prix_m2_falls_back_to_constant():
    """prix_m2 = 0 (colonne absente en DB) retombe sur la constante."""
    code = "75003"
    raw = _base_raw_row(code)
    raw["prix_m2"] = 0.0
    row = _enrich_district_row(code, raw)
    assert row["prix_m2"] == pytest.approx(PRIX_M2_BASES[code])


def test_none_prix_m2_falls_back_to_constant():
    code = "75005"
    raw = _base_raw_row(code)
    raw["prix_m2"] = None
    row = _enrich_district_row(code, raw)
    assert row["prix_m2"] == pytest.approx(PRIX_M2_BASES[code])


# ── Champs dérivés ────────────────────────────────────────────────────────────

def test_m2_abordables_is_computed():
    code = "75011"
    row = _enrich_district_row(code, _base_raw_row(code))
    assert "m2_abordables" in row
    assert row["m2_abordables"] > 0
    # Cohérence : revenu_median / prix_m2
    expected = round(row["revenu_median"] / row["prix_m2"], 2)
    assert row["m2_abordables"] == pytest.approx(expected, abs=0.01)


def test_accessibilite_idx_is_in_range():
    code = "75019"
    row = _enrich_district_row(code, _base_raw_row(code))
    assert "accessibilite_idx" in row
    assert 0 <= row["accessibilite_idx"] <= 100


def test_m2_abordables_updates_with_real_prices():
    """Avec des vraies valeurs, m2_abordables est cohérent."""
    code = "75007"
    raw = _base_raw_row(code)
    raw["prix_m2"] = 16_000.0
    raw["revenu_median"] = 48_000.0
    row = _enrich_district_row(code, raw)
    assert row["m2_abordables"] == pytest.approx(48_000.0 / 16_000.0, abs=0.01)


# ── Tous les arrondissements ──────────────────────────────────────────────────

def test_all_districts_enrich_without_error():
    """Tous les 20 arrondissements s'enrichissent sans exception."""
    for i in range(1, 21):
        code = f"750{i:02d}"
        row = _enrich_district_row(code, _base_raw_row(code))
        assert row["code"] == code
        assert row["prix_m2"] > 0
        assert row["revenu_median"] > 0
        assert 0 <= row["score"] <= 100
