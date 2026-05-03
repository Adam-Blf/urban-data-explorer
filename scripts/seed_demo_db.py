"""Seed un `urban.duckdb` de démo, sans dépendre du pipeline complet.

Crée toutes les tables Gold avec des données réalistes synthétiques pour les
20 arrondissements de Paris, basées sur des ordres de grandeur publics
(prix DVF 2024, populations INSEE, équipements OpenData Paris).

Permet à l'API + au frontend de démarrer immédiatement sans télécharger
les ~500 MB de DVF/POI bruts. Le `urban.duckdb` produit fait < 500 KB.

Usage::

    python scripts/seed_demo_db.py
    # → écrit data/gold/urban.duckdb
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "demo" / "urban.duckdb"

# ---------------------------------------------------------------------------
# Snapshot Paris 2024 · ordres de grandeur publics (Insee, OpenData Paris, DVF)
# ---------------------------------------------------------------------------

ARRONDISSEMENTS = [
    # code,    label,                centroid_lon, centroid_lat, population, parc, prix_m2, transactions, log_sociaux, revenu_med
    ("75101", "1er arrondissement",   2.337, 48.862,  16_888,  10_500, 14_200,   320,    18,  37_400),
    ("75102", "2e arrondissement",    2.347, 48.868,  20_796,  14_300, 13_100,   430,    25,  35_800),
    ("75103", "3e arrondissement",    2.362, 48.863,  35_011,  23_000, 13_700,   780,    65,  35_100),
    ("75104", "4e arrondissement",    2.357, 48.854,  27_487,  19_400, 14_600,   600,    45,  37_900),
    ("75105", "5e arrondissement",    2.350, 48.844,  58_283,  35_000, 13_400, 1_280,   105,  35_400),
    ("75106", "6e arrondissement",    2.333, 48.849,  40_580,  28_000, 16_800,   910,    62,  44_900),
    ("75107", "7e arrondissement",    2.312, 48.856,  49_988,  31_500, 16_500, 1_120,    72,  46_200),
    ("75108", "8e arrondissement",    2.318, 48.872,  35_879,  25_700, 15_300,   840,    55,  43_800),
    ("75109", "9e arrondissement",    2.337, 48.877,  58_730,  42_000, 12_800, 1_390,   210,  31_700),
    ("75110", "10e arrondissement",   2.361, 48.876,  89_603,  60_500, 11_200, 2_010,   460,  25_300),
    ("75111", "11e arrondissement",   2.380, 48.859, 144_492,  91_000, 11_400, 3_240,   620,  27_900),
    ("75112", "12e arrondissement",   2.421, 48.835, 138_188,  80_700, 10_500, 2_750,   730,  29_400),
    ("75113", "13e arrondissement",   2.362, 48.829, 178_544, 105_000,  9_700, 3_410, 1_280,  25_100),
    ("75114", "14e arrondissement",   2.327, 48.829, 137_105,  84_500, 11_100, 2_780,   780,  30_200),
    ("75115", "15e arrondissement",   2.300, 48.840, 233_392, 142_500, 11_700, 4_510,   910,  33_500),
    ("75116", "16e arrondissement",   2.262, 48.860, 166_851, 108_000, 12_300, 3_120,   480,  41_700),
    ("75117", "17e arrondissement",   2.307, 48.887, 167_835, 109_500, 11_500, 3_280,   870,  31_400),
    ("75118", "18e arrondissement",   2.349, 48.892, 197_309, 121_300,  9_500, 3_790, 1_860,  21_300),
    ("75119", "19e arrondissement",   2.385, 48.887, 184_787, 110_000,  8_900, 3_410, 2_240,  20_100),
    ("75120", "20e arrondissement",   2.401, 48.863, 193_098, 117_400,  9_200, 3_640, 2_010,  21_700),
]

POI_DENSITY_PER_ARR = {
    # arr ends → (transport, service_public, commerce, culture, sante, environnement)
    "01": (45, 18, 12, 38, 5,  4),
    "02": (52, 22, 14, 28, 6,  3),
    "03": (62, 28, 18, 35, 8,  6),
    "04": (58, 24, 16, 42, 7,  5),
    "05": (78, 38, 22, 48, 12, 9),
    "06": (60, 26, 20, 38, 10, 7),
    "07": (72, 32, 18, 44, 14, 11),
    "08": (68, 28, 22, 36, 13, 8),
    "09": (90, 42, 28, 32, 11, 10),
    "10": (110, 56, 36, 26, 16, 14),
    "11": (134, 64, 42, 30, 18, 17),
    "12": (128, 60, 38, 24, 20, 22),
    "13": (140, 78, 40, 22, 24, 26),
    "14": (118, 60, 36, 24, 18, 20),
    "15": (158, 82, 46, 26, 22, 24),
    "16": (124, 60, 30, 30, 17, 28),
    "17": (138, 70, 40, 22, 18, 18),
    "18": (146, 80, 50, 28, 20, 20),
    "19": (138, 76, 44, 24, 22, 32),
    "20": (140, 78, 46, 22, 21, 26),
}

POI_NAMES = {
    "transport": ["Vélib", "Belib", "Station Métro", "Piste cyclable"],
    "service_public": ["École élémentaire", "Collège", "Sanisette", "Mairie"],
    "commerce": ["Marché découvert", "Boutique de quartier", "Halle"],
    "culture": ["Musée", "Monument historique", "Cinéma", "Bibliothèque"],
    "sante": ["Hôpital", "Clinique", "Centre médical"],
    "environnement": ["Square", "Parc", "Jardin partagé"],
}


def _seasonal_price(base: float, year: int, month: int) -> float:
    """Prix m² mensuel · trend annuel + saisonnalité douce + bruit fixe."""
    yidx = year - 2019
    trend = base * (1 + 0.018 * yidx - 0.005 * max(0, yidx - 3))   # plateau post-2022
    seasonal = 1 + 0.018 * math.sin((month - 3) / 12 * 2 * math.pi)
    rng = random.Random(f"{year}{month}{base}")
    noise = 1 + (rng.random() - 0.5) * 0.012
    return round(trend * seasonal * noise, 1)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    con = duckdb.connect(OUT.as_posix())

    # --- dim_arrondissement ---
    con.execute("""
        CREATE TABLE dim_arrondissement (
            code_arrondissement VARCHAR PRIMARY KEY,
            label               VARCHAR,
            centroid_lon        DOUBLE,
            centroid_lat        DOUBLE,
            area_km2            DOUBLE
        );
    """)
    for code, label, lon, lat, *_ in ARRONDISSEMENTS:
        con.execute(
            "INSERT INTO dim_arrondissement VALUES (?, ?, ?, ?, ?)",
            [code, label, lon, lat, round(0.7 + (int(code[-2:]) % 7) * 0.4, 2)],
        )

    # --- fact_revenus_arr ---
    con.execute("""
        CREATE TABLE fact_revenus_arr (
            code_arrondissement VARCHAR,
            MED21               DOUBLE,
            PIMP21              DOUBLE,
            TP6021              DOUBLE
        );
    """)
    for code, *_, revenu in ARRONDISSEMENTS:
        # PIMP : part des foyers fiscaux imposés. TP60 : taux de pauvreté.
        pimp = 60 + (revenu - 20_000) / 700
        tp = max(8, 30 - (revenu - 20_000) / 1_500)
        con.execute(
            "INSERT INTO fact_revenus_arr VALUES (?, ?, ?, ?)",
            [code, float(revenu), round(pimp, 1), round(tp, 1)],
        )

    # --- fact_logements_sociaux ---
    con.execute("""
        CREATE TABLE fact_logements_sociaux (
            code_arrondissement   VARCHAR,
            year                  INTEGER,
            nb_logements_finances INTEGER
        );
    """)
    for code, _label, _lon, _lat, _pop, _parc, _prix, _tx, log_total, _rev in ARRONDISSEMENTS:
        for year in range(2019, 2025):
            yfrac = 0.12 + 0.04 * (year - 2019)
            con.execute(
                "INSERT INTO fact_logements_sociaux VALUES (?, ?, ?)",
                [code, year, max(0, int(log_total * yfrac / 6))],
            )

    # --- fact_air_quality ---
    con.execute("""
        CREATE TABLE fact_air_quality (
            date_heure      VARCHAR,
            no2             DOUBLE,
            o3              DOUBLE,
            pm10            DOUBLE,
            pm25            DOUBLE,
            aqi_mean_paris  DOUBLE
        );
    """)
    for month in range(1, 13):
        no2 = round(28 + 10 * math.cos(month / 12 * 2 * math.pi), 1)
        o3 = round(35 + 25 * math.sin(month / 12 * 2 * math.pi - 0.5), 1)
        pm10 = round(18 + 4 * math.sin(month / 12 * 2 * math.pi), 1)
        pm25 = round(11 + 2 * math.sin(month / 12 * 2 * math.pi), 1)
        aqi = round((no2 + o3 + pm10 + pm25) / 4, 1)
        con.execute(
            "INSERT INTO fact_air_quality VALUES (?, ?, ?, ?, ?, ?)",
            [f"2024-{month:02d}-15T12:00:00Z", no2, o3, pm10, pm25, aqi],
        )

    # --- fact_transactions_arr_mois ---
    con.execute("""
        CREATE TABLE fact_transactions_arr_mois (
            code_arrondissement VARCHAR,
            year                INTEGER,
            month               INTEGER,
            nb_transactions     INTEGER,
            prix_m2_median      DOUBLE,
            prix_m2_moyen       DOUBLE,
            prix_m2_p25         DOUBLE,
            prix_m2_p75         DOUBLE,
            volume_eur          DOUBLE
        );
    """)
    for code, _label, _lon, _lat, _pop, _parc, base_price, annual_tx, _log, _rev in ARRONDISSEMENTS:
        for year in range(2019, 2025):
            for month in range(1, 13):
                price = _seasonal_price(base_price, year, month)
                rng = random.Random(f"{code}{year}{month}")
                nb = max(5, int(annual_tx / 12 * (0.8 + rng.random() * 0.4)))
                con.execute(
                    "INSERT INTO fact_transactions_arr_mois VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [code, year, month, nb, price, round(price * 1.04, 1),
                     round(price * 0.85, 1), round(price * 1.18, 1),
                     round(price * 50 * nb, 1)],
                )

    # --- fact_poi_arr + dim_poi ---
    con.execute("""
        CREATE TABLE fact_poi_arr (
            code_arrondissement VARCHAR,
            category            VARCHAR,
            subcategory         VARCHAR,
            nb_poi              BIGINT
        );
        CREATE TABLE dim_poi (
            code_arrondissement VARCHAR,
            category            VARCHAR,
            subcategory         VARCHAR,
            name                VARCHAR,
            lon                 DOUBLE,
            lat                 DOUBLE
        );
    """)
    cats = ["transport", "service_public", "commerce", "culture", "sante", "environnement"]
    for code, _label, lon, lat, *_ in ARRONDISSEMENTS:
        densities = POI_DENSITY_PER_ARR[code[-2:]]
        for cat, total in zip(cats, densities, strict=False):
            sub = POI_NAMES[cat][0]
            con.execute(
                "INSERT INTO fact_poi_arr VALUES (?, ?, ?, ?)",
                [code, cat, sub, total],
            )
            rng = random.Random(f"{code}{cat}")
            for i in range(min(total, 30)):  # cap at 30 points/cat for the map
                px = round(lon + (rng.random() - 0.5) * 0.02, 6)
                py = round(lat + (rng.random() - 0.5) * 0.014, 6)
                name = f"{sub} {code[-2:]}-{i+1:02d}"
                con.execute(
                    "INSERT INTO dim_poi VALUES (?, ?, ?, ?, ?, ?)",
                    [code, cat, sub, name, px, py],
                )

    # --- kpi_arrondissement ---
    con.execute("""
        CREATE TABLE kpi_arrondissement AS
        WITH pois AS (
            SELECT
                code_arrondissement,
                SUM(CASE WHEN category = 'transport'      THEN nb_poi ELSE 0 END) AS nb_transport,
                SUM(CASE WHEN category = 'service_public' THEN nb_poi ELSE 0 END) AS nb_service_public,
                SUM(CASE WHEN category = 'commerce'       THEN nb_poi ELSE 0 END) AS nb_commerce,
                SUM(CASE WHEN category = 'culture'        THEN nb_poi ELSE 0 END) AS nb_culture,
                SUM(CASE WHEN category = 'sante'          THEN nb_poi ELSE 0 END) AS nb_sante,
                SUM(CASE WHEN category = 'environnement'  THEN nb_poi ELSE 0 END) AS nb_environnement
            FROM fact_poi_arr
            GROUP BY code_arrondissement
        ),
        pop AS (SELECT * FROM (VALUES
""" + ",\n".join(
        f"('{c}', {p}, {pa})" for c, _, _, _, p, pa, *_ in ARRONDISSEMENTS
    ) + """
        ) AS t(code_arrondissement, population, parc_logements)),
        base AS (
            SELECT
                d.code_arrondissement,
                d.label,
                d.centroid_lon,
                d.centroid_lat,
                pop.population,
                pop.parc_logements,
                r.MED21 AS revenu_median,
                (SELECT MEDIAN(prix_m2_median) FROM fact_transactions_arr_mois f
                  WHERE f.code_arrondissement = d.code_arrondissement AND f.year = 2024) AS prix_m2,
                (SELECT SUM(nb_transactions)   FROM fact_transactions_arr_mois f
                  WHERE f.code_arrondissement = d.code_arrondissement AND f.year = 2024) AS transactions_an,
                (SELECT SUM(nb_logements_finances) FROM fact_logements_sociaux s
                  WHERE s.code_arrondissement = d.code_arrondissement) AS log_sociaux_finances,
                (SELECT AVG(aqi_mean_paris) FROM fact_air_quality) AS aqi_paris,
                COALESCE(p.nb_transport, 0)      AS nb_transport,
                COALESCE(p.nb_service_public, 0) AS nb_service_public,
                COALESCE(p.nb_commerce, 0)       AS nb_commerce,
                COALESCE(p.nb_culture, 0)        AS nb_culture,
                COALESCE(p.nb_sante, 0)          AS nb_sante,
                COALESCE(p.nb_environnement, 0)  AS nb_environnement
            FROM dim_arrondissement d
            LEFT JOIN pop USING (code_arrondissement)
            LEFT JOIN fact_revenus_arr r USING (code_arrondissement)
            LEFT JOIN pois p USING (code_arrondissement)
        ),
        scored AS (
            SELECT *,
                CASE WHEN prix_m2 = 0 THEN NULL ELSE revenu_median / (prix_m2 * 50.0) END AS idx_accessibilite,
                CASE WHEN parc_logements = 0 THEN NULL ELSE transactions_an * 1000.0 / parc_logements END AS idx_tension,
                CASE WHEN population = 0 THEN NULL ELSE log_sociaux_finances * 10000.0 / population END AS idx_effort_social,
                CASE WHEN population = 0 THEN 0
                     ELSE (nb_transport + nb_culture + nb_sante + nb_environnement) * 1000.0 / population
                END AS poi_density
            FROM base
        ),
        zscored AS (
            SELECT *,
                (idx_accessibilite - AVG(idx_accessibilite) OVER ())
                    / NULLIF(STDDEV_SAMP(idx_accessibilite) OVER (), 0) AS z_a,
                (idx_tension - AVG(idx_tension) OVER ())
                    / NULLIF(STDDEV_SAMP(idx_tension) OVER (), 0) AS z_t,
                (idx_effort_social - AVG(idx_effort_social) OVER ())
                    / NULLIF(STDDEV_SAMP(idx_effort_social) OVER (), 0) AS z_e,
                (poi_density - AVG(poi_density) OVER ())
                    / NULLIF(STDDEV_SAMP(poi_density) OVER (), 0) AS z_p
            FROM scored
        )
        SELECT
            code_arrondissement, label, centroid_lon, centroid_lat,
            population, parc_logements, revenu_median, prix_m2,
            transactions_an, log_sociaux_finances, aqi_paris,
            nb_transport, nb_service_public, nb_commerce,
            nb_culture, nb_sante, nb_environnement,
            idx_accessibilite, idx_tension, idx_effort_social,
            (COALESCE(z_a,0)*0.30 + COALESCE(z_p,0)*0.40
             + COALESCE(z_e,0)*0.15 + COALESCE(-z_t,0)*0.15) AS idx_attractivite
        FROM zscored
        ORDER BY code_arrondissement;
    """)

    # --- timeline_arrondissement ---
    con.execute("""
        CREATE TABLE timeline_arrondissement AS
        SELECT
            code_arrondissement, year, month,
            CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS year_month,
            prix_m2_median, nb_transactions, volume_eur,
            AVG(prix_m2_median) OVER (
                PARTITION BY code_arrondissement
                ORDER BY year, month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS prix_m2_median_3m,
            prix_m2_median - LAG(prix_m2_median) OVER (
                PARTITION BY code_arrondissement ORDER BY year, month
            ) AS delta_prix_m2_mom
        FROM fact_transactions_arr_mois
        ORDER BY code_arrondissement, year, month;
    """)

    con.commit()

    # Sanity check
    n_arr = con.execute("SELECT COUNT(*) FROM kpi_arrondissement").fetchone()[0]
    n_tx  = con.execute("SELECT COUNT(*) FROM fact_transactions_arr_mois").fetchone()[0]
    n_poi = con.execute("SELECT COUNT(*) FROM dim_poi").fetchone()[0]
    n_tl  = con.execute("SELECT COUNT(*) FROM timeline_arrondissement").fetchone()[0]
    con.close()

    size_kb = OUT.stat().st_size / 1024
    print(f"Seeded {OUT}")
    print(f"  arr={n_arr} · tx={n_tx} · poi={n_poi} · timeline={n_tl} · {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
