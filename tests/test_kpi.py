"""Tests métier · cohérence des KPIs et des indicateurs composites."""

from __future__ import annotations

import os

import duckdb
import pytest


@pytest.fixture(scope="module")
def gold():
    path = os.environ.get("GOLD_DUCKDB_PATH", "./data/demo/urban.duckdb")
    con = duckdb.connect(path, read_only=True)
    yield con
    con.close()


def test_20_arrondissements(gold):
    rows = gold.execute("SELECT COUNT(*) FROM kpi_arrondissement").fetchone()
    assert rows[0] == 20


def test_codes_normalized(gold):
    bad = gold.execute("""
        SELECT COUNT(*) FROM kpi_arrondissement
        WHERE code_arrondissement NOT LIKE '751%' OR LENGTH(code_arrondissement) != 5
    """).fetchone()[0]
    assert bad == 0


def test_indicators_finite(gold):
    bad = gold.execute("""
        SELECT COUNT(*) FROM kpi_arrondissement
        WHERE idx_accessibilite IS NULL
           OR idx_tension IS NULL
           OR idx_effort_social IS NULL
           OR idx_attractivite IS NULL
    """).fetchone()[0]
    assert bad == 0, "every arrondissement must have all 4 composite indicators"


def test_attractivite_centered(gold):
    avg = gold.execute("SELECT AVG(idx_attractivite) FROM kpi_arrondissement").fetchone()[0]
    # composite z-score · should be ~0 by construction
    assert abs(avg) < 0.05, f"idx_attractivite mean should be ~0, got {avg}"


def test_prix_m2_realistic(gold):
    bad = gold.execute("""
        SELECT COUNT(*) FROM kpi_arrondissement
        WHERE prix_m2 < 5000 OR prix_m2 > 25000
    """).fetchone()[0]
    assert bad == 0, "prix_m2 must stay within Paris market range"


def test_timeline_continuous(gold):
    """Each arrondissement has 6 years × 12 months = 72 timeline points."""
    rows = gold.execute("""
        SELECT code_arrondissement, COUNT(*) AS n
        FROM timeline_arrondissement
        GROUP BY code_arrondissement
    """).fetchall()
    assert len(rows) == 20
    assert all(n == 72 for _, n in rows)


def test_poi_categories_present(gold):
    cats = gold.execute("SELECT DISTINCT category FROM fact_poi_arr ORDER BY category").fetchall()
    expected = {"commerce", "culture", "environnement", "sante", "service_public", "transport"}
    assert {c[0] for c in cats} == expected
