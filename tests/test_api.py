"""Tests d'intégration · démarre l'app FastAPI in-process et tape ses endpoints."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module=None):
    # Use the committed demo DB
    os.environ.setdefault("GOLD_DUCKDB_PATH", "./data/demo/urban.duckdb")
    os.environ.setdefault("JWT_SECRET", "test-secret-thirty-two-chars-aaaaaaaa")
    os.environ.setdefault("DEMO_USER", "admin")
    os.environ.setdefault("DEMO_PASSWORD", "admin")

    # Reset settings singleton so the env above is picked up
    import pipeline.config
    pipeline.config._settings = None

    from api.main import app
    return TestClient(app)


def _login(client) -> str:
    r = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token
    return token


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_bad_credentials_rejected(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_arrondissements_requires_auth(client):
    r = client.get("/datamarts/arrondissements")
    assert r.status_code == 401


def test_arrondissements_pagination(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}

    r = client.get("/datamarts/arrondissements?page=1&page_size=5", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert len(body["items"]) == 5
    assert body["total"] == 20  # 20 arrondissements
    assert body["pages"] == 4
    assert body["next_page"] == 2
    assert body["prev_page"] is None


def test_arrondissements_filter_by_code(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get(
        "/datamarts/arrondissements?code_arrondissement=75108",
        headers=h,
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["code_arrondissement"] == "75108"


def test_arrondissements_ordering(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get(
        "/datamarts/arrondissements?order_by=prix_m2&desc=true&page_size=5",
        headers=h,
    )
    items = r.json()["items"]
    prices = [it["prix_m2"] for it in items if it["prix_m2"] is not None]
    assert prices == sorted(prices, reverse=True)


def test_timeline_filter_year_range(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get(
        "/datamarts/timeline?code_arrondissement=75108&year_from=2024&year_to=2024&page_size=20",
        headers=h,
    )
    body = r.json()
    assert body["total"] == 12  # 12 mois 2024
    assert all(p["year"] == 2024 for p in body["items"])


def test_indicators_filter(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get(
        "/datamarts/indicators?indicator=idx_attractivite&page_size=50",
        headers=h,
    )
    body = r.json()
    assert body["total"] == 20
    assert all(it["indicator"] == "idx_attractivite" for it in body["items"])


def test_geojson_arrondissements(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get("/geo/arrondissements.geojson", headers=h)
    # If the raw geojson hasn't been ingested locally, the endpoint returns 404 ·
    # the demo seed only ships gold, not raw, so accept either case.
    assert r.status_code in (200, 404)


def test_poi_geojson_filter_category(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get("/geo/poi.geojson?category=transport&limit=100", headers=h)
    assert r.status_code == 200
    payload = r.json()
    assert payload["type"] == "FeatureCollection"
    assert all(f["properties"]["category"] == "transport"
               for f in payload["features"])
