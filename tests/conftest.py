"""Fixtures partagées pour la suite de tests Urban Data Explorer."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app_client():
    """Client FastAPI partagé pour toute la session de tests.

    Le scope 'session' évite de recréer l'app (et recalculer DEMO_USERS
    avec PBKDF2) à chaque test.
    """
    from api.main import app
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture(autouse=True)
def _clear_quota_hits():
    """Vide les compteurs de quota avant chaque test pour l'isolation.

    Sans ça, les requêtes émises par un test influenceraient les limites
    des tests suivants (même IP 'testclient' dans TestClient).
    """
    from api import security
    security._hits.clear()
    yield
    security._hits.clear()
