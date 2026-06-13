"""Tests d'authentification JWT : encode/decode, expiration, mots de passe."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import jwt
import pytest

from api.security import (
    JWT_ALGORITHM,
    JWT_SECRET,
    authenticate,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── hash / verify ────────────────────────────────────────────────────────────

def test_hash_verify_roundtrip():
    h = hash_password("secret123")
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_hash_different_salts():
    h1 = hash_password("same")
    h2 = hash_password("same")
    # Deux hash du même mot de passe avec des sels aléatoires différents
    assert h1 != h2
    assert verify_password("same", h1) is True
    assert verify_password("same", h2) is True


def test_hash_malformed_stored():
    assert verify_password("x", "no_dollar_sign") is False


# ── authenticate ─────────────────────────────────────────────────────────────

def test_authenticate_demo_valid():
    user = authenticate("demo", "demo")
    assert user is not None
    assert user["username"] == "demo"
    assert user["role"] == "viewer"


def test_authenticate_admin_valid():
    user = authenticate("admin", "admin")
    assert user is not None
    assert user["role"] == "admin"


def test_authenticate_wrong_password():
    assert authenticate("demo", "wrongpass") is None


def test_authenticate_unknown_user():
    assert authenticate("nobody", "demo") is None


def test_authenticate_empty_credentials():
    assert authenticate("", "") is None


# ── create / decode token ─────────────────────────────────────────────────────

def test_token_roundtrip():
    token = create_access_token("demo", "viewer")
    result = decode_token(token)
    assert result is not None
    assert result["username"] == "demo"
    assert result["role"] == "viewer"


def test_token_admin_roundtrip():
    token = create_access_token("admin", "admin")
    result = decode_token(token)
    assert result is not None
    assert result["role"] == "admin"


def test_expired_token_rejected():
    """Un jeton expiré doit être rejeté par decode_token."""
    payload = {
        "sub": "demo",
        "role": "viewer",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    assert decode_token(expired) is None


def test_token_wrong_secret_rejected():
    """Un jeton signé avec un autre secret doit être rejeté."""
    payload = {"sub": "demo", "role": "viewer", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    bad_token = jwt.encode(payload, "wrong-secret", algorithm=JWT_ALGORITHM)
    assert decode_token(bad_token) is None


def test_garbage_token_rejected():
    assert decode_token("not.a.token") is None


def test_empty_string_rejected():
    assert decode_token("") is None


def test_malformed_header_rejected():
    # Header valide, payload invalide
    assert decode_token("eyJhbGciOiJIUzI1NiJ9.invalid_payload.sig") is None
