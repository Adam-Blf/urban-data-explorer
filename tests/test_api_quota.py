"""Tests de quota : tiers anonyme vs authentifié, comportement 429."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from api import security
from api.security import create_access_token


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hit_n_times(client, n: int, path: str = "/health", headers: dict | None = None) -> list:
    responses = []
    for _ in range(n):
        r = client.get(path, headers=headers or {})
        responses.append(r)
    return responses


# ── Tier anonyme ─────────────────────────────────────────────────────────────

def test_anon_below_limit(app_client):
    """Sous la limite : toutes les requêtes réussissent."""
    with patch.object(security, "QUOTA_ANON", 5), patch.object(security, "QUOTA_AUTH", 600):
        resps = _hit_n_times(app_client, 5)
    assert all(r.status_code == 200 for r in resps)


def test_anon_at_limit_triggers_429(app_client):
    """Dès que la limite est dépassée, la suivante reçoit 429."""
    with patch.object(security, "QUOTA_ANON", 2), patch.object(security, "QUOTA_AUTH", 600):
        app_client.get("/health")
        app_client.get("/health")
        r = app_client.get("/health")
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_429_detail_message(app_client):
    """Le corps de la réponse 429 contient le message d'erreur attendu."""
    with patch.object(security, "QUOTA_ANON", 1), patch.object(security, "QUOTA_AUTH", 600):
        app_client.get("/health")
        r = app_client.get("/health")
    assert r.status_code == 429
    assert "Quota" in r.json().get("detail", "")


# ── Fix #2 : token invalide ne doit PAS élever le quota ─────────────────────

def test_invalid_bearer_stays_in_anon_tier(app_client):
    """Un token Bearer invalide → tier anonyme (pas le tier AUTH élargi)."""
    headers = {"Authorization": "Bearer this-is-not-a-valid-jwt"}
    with patch.object(security, "QUOTA_ANON", 2), patch.object(security, "QUOTA_AUTH", 600):
        app_client.get("/health", headers=headers)
        app_client.get("/health", headers=headers)
        r = app_client.get("/health", headers=headers)
    # Token invalide → tier anon → 429 à la 3ème requête
    assert r.status_code == 429


def test_no_bearer_prefix_stays_anon(app_client):
    """Authorization sans préfixe 'Bearer' → tier anonyme."""
    headers = {"Authorization": create_access_token("demo", "viewer")}
    with patch.object(security, "QUOTA_ANON", 2), patch.object(security, "QUOTA_AUTH", 600):
        app_client.get("/health", headers=headers)
        app_client.get("/health", headers=headers)
        r = app_client.get("/health", headers=headers)
    assert r.status_code == 429


# ── Tier authentifié avec token valide ───────────────────────────────────────

def test_valid_token_uses_auth_tier(app_client):
    """Un token JWT valide doit utiliser le quota élargi QUOTA_AUTH."""
    token = create_access_token("demo", "viewer")
    headers = {"Authorization": f"Bearer {token}"}
    with patch.object(security, "QUOTA_ANON", 2), patch.object(security, "QUOTA_AUTH", 10):
        resps = _hit_n_times(app_client, 5, headers=headers)
    # 5 requêtes avec limit=10 → toutes OK
    assert all(r.status_code == 200 for r in resps)


def test_valid_token_still_rate_limited(app_client):
    """Même un token valide est limité une fois QUOTA_AUTH atteint."""
    token = create_access_token("demo", "viewer")
    headers = {"Authorization": f"Bearer {token}"}
    with patch.object(security, "QUOTA_ANON", 120), patch.object(security, "QUOTA_AUTH", 3):
        app_client.get("/health", headers=headers)
        app_client.get("/health", headers=headers)
        app_client.get("/health", headers=headers)
        r = app_client.get("/health", headers=headers)
    assert r.status_code == 429
