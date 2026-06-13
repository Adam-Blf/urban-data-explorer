"""Tests des endpoints FastAPI via TestClient (sans Docker)."""

from __future__ import annotations

import pytest


# ── /health ──────────────────────────────────────────────────────────────────

def test_health_ok(app_client):
    r = app_client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["mode"] == "local-first"
    assert data["districts"] == 20


def test_root_returns_json(app_client):
    r = app_client.get("/")
    assert r.status_code == 200


# ── /datamarts/dashboard ──────────────────────────────────────────────────────

def test_dashboard_returns_20_districts(app_client):
    r = app_client.get("/datamarts/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 20


def test_dashboard_response_schema(app_client):
    r = app_client.get("/datamarts/dashboard")
    row = r.json()[0]
    # Champs de base
    assert "code" in row
    assert "name" in row
    assert "score" in row
    assert "prix_m2" in row
    assert "revenu_median" in row
    # Champs ajoutés par fix #4
    assert "m2_abordables" in row
    assert "accessibilite_idx" in row
    assert "data_source" in row


def test_dashboard_filter_arrondissement(app_client):
    r = app_client.get("/datamarts/dashboard?arrondissement=75011")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["code"] == "75011"


def test_dashboard_filter_score_min(app_client):
    r = app_client.get("/datamarts/dashboard?score_min=0")
    assert r.status_code == 200
    assert len(r.json()) == 20


def test_dashboard_sort_by_score(app_client):
    r = app_client.get("/datamarts/dashboard?sort=score")
    assert r.status_code == 200
    scores = [row["score"] for row in r.json()]
    assert scores == sorted(scores, reverse=True)


def test_dashboard_unknown_arrondissement(app_client):
    r = app_client.get("/datamarts/dashboard?arrondissement=75999")
    assert r.status_code == 200
    assert r.json() == []


# ── /datamarts/overview ───────────────────────────────────────────────────────

def test_overview_shape(app_client):
    r = app_client.get("/datamarts/overview")
    assert r.status_code == 200
    data = r.json()
    assert data["district_count"] == 20
    assert data["source_count"] > 0


# ── /auth/token ───────────────────────────────────────────────────────────────

def test_login_demo_valid(app_client):
    r = app_client.post("/auth/token", data={"username": "demo", "password": "demo"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["role"] == "viewer"


def test_login_admin_valid(app_client):
    r = app_client.post("/auth/token", data={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_login_invalid_credentials(app_client):
    r = app_client.post("/auth/token", data={"username": "demo", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(app_client):
    r = app_client.post("/auth/token", data={"username": "ghost", "password": "x"})
    assert r.status_code == 401


# ── /auth/me (route protégée admin) ──────────────────────────────────────────

def test_me_no_token_401(app_client):
    r = app_client.get("/auth/me")
    assert r.status_code == 401


def test_me_viewer_token_403(app_client):
    """Un token viewer (non admin) doit recevoir 403 sur /auth/me."""
    login = app_client.post("/auth/token", data={"username": "demo", "password": "demo"})
    token = login.json()["access_token"]
    r = app_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_me_admin_token_200(app_client):
    """Un token admin doit accéder à /auth/me."""
    login = app_client.post("/auth/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    r = app_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["authenticated"] is True


# ── /pipeline/latest ──────────────────────────────────────────────────────────

def test_pipeline_latest(app_client):
    r = app_client.get("/pipeline/latest")
    # Retourne soit un PipelineRun, soit null (aucun run enregistré)
    assert r.status_code == 200


# ── /pipeline/metrics ─────────────────────────────────────────────────────────

def test_pipeline_metrics_endpoint(app_client):
    r = app_client.get("/pipeline/metrics")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── /catalog ─────────────────────────────────────────────────────────────────

def test_catalog_sources(app_client):
    r = app_client.get("/catalog/sources")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 24  # 24 sources dans le catalogue


# ── /metrics (Prometheus scrape endpoint) ─────────────────────────────────────

def test_metrics_responds_200(app_client):
    """Le scrape endpoint Prometheus doit répondre 200 sans authentification."""
    r = app_client.get("/metrics")
    assert r.status_code == 200


def test_metrics_content_type(app_client):
    """La réponse doit être au format texte Prometheus."""
    r = app_client.get("/metrics")
    assert "text/plain" in r.headers.get("content-type", "")


def test_metrics_contains_ude_counters(app_client):
    """La réponse doit exposer les compteurs ude_http_requests_total."""
    # Émettre au moins une requête pour peupler les compteurs
    app_client.get("/health")
    r = app_client.get("/metrics")
    body = r.text
    assert "ude_http_requests_total" in body
    assert "ude_http_request_duration_seconds" in body


# ── /search/semantic ──────────────────────────────────────────────────────────

def test_semantic_search_responds_200(app_client):
    """La recherche sémantique doit répondre 200 avec un terme quelconque."""
    r = app_client.get("/search/semantic?q=musée")
    assert r.status_code == 200


def test_semantic_search_returns_list(app_client):
    r = app_client.get("/search/semantic?q=parc nature")
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_semantic_search_result_schema(app_client):
    """Chaque résultat doit avoir code, description et score."""
    r = app_client.get("/search/semantic?q=logement")
    data = r.json()
    assert len(data) >= 1
    first = data[0]
    assert "code" in first
    assert "description" in first
    assert "score" in first
    # Le score de similarité cosinus est dans [0, 1]
    assert 0.0 <= first["score"] <= 1.0


def test_semantic_search_top_k(app_client):
    """Le paramètre top_k doit limiter le nombre de résultats."""
    r = app_client.get("/search/semantic?q=tourisme&top_k=3")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_semantic_search_missing_q(app_client):
    """Un appel sans ?q= doit retourner 422 (validation Pydantic)."""
    r = app_client.get("/search/semantic")
    assert r.status_code == 422
