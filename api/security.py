"""Sécurité de l'API · C2.1 (authentification + autorisations/quotas).

- Authentification : OAuth2 password flow -> jeton JWT signé (HS256).
- Autorisations : rôles (viewer / admin) portés par le jeton.
- Quotas : limiteur de débit par IP, à fenêtre glissante (anonyme vs authentifié).

Choix assumé : la lecture des datamarts reste publique (dashboard ouvert),
mais l'authentification ouvre un quota élargi et les routes d'administration.
Le secret JWT provient de la variable d'environnement UDE_JWT_SECRET.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# ════════════════════════════════════════════════════════════════════════
# 1) CONFIGURATION · les réglages, regroupés en haut pour être faciles à trouver
# ════════════════════════════════════════════════════════════════════════
# Clé secrète qui signe les jetons. En production, la définir via une variable
# d'environnement (UDE_JWT_SECRET) ; ici une valeur par défaut pour le dev.
JWT_SECRET = os.getenv("UDE_JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"   # algorithme de signature du jeton
TOKEN_TTL_MIN = 60         # durée de vie d'un jeton : 60 minutes

# Quotas = nombre maximum de requêtes autorisées par IP sur 60 secondes.
QUOTA_ANON = 120   # visiteur non connecté
QUOTA_AUTH = 600   # utilisateur connecté (quota élargi = avantage de se connecter)
QUOTA_WINDOW_S = 60  # taille de la fenêtre de comptage, en secondes

# Indique a FastAPI ou recuperer le jeton (en-tete "Authorization: Bearer ...").
# auto_error=False -> pas d'erreur si absent : la lecture publique reste permise.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

# ════════════════════════════════════════════════════════════════════════
# 2) MOTS DE PASSE · on ne stocke jamais le mot de passe en clair
# ════════════════════════════════════════════════════════════════════════
# On stocke une empreinte (hash) PBKDF2-HMAC-SHA256 : salée + 200 000 itérations.
# Impossible de remonter au mot de passe d'origine depuis l'empreinte.
_PBKDF2_ROUNDS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _PBKDF2_ROUNDS)
    return hmac.compare_digest(dk.hex(), dk_hex)


# Utilisateurs de démonstration (en prod : table SGBD)
DEMO_USERS: dict[str, dict] = {
    "demo": {"password_hash": hash_password("demo"), "role": "viewer"},
    "admin": {"password_hash": hash_password("admin"), "role": "admin"},
}


# ════════════════════════════════════════════════════════════════════════
# 3) AUTHENTIFICATION · verifier l'identite, puis fabriquer/lire un jeton JWT
# ════════════════════════════════════════════════════════════════════════
def authenticate(username: str, password: str) -> dict | None:
    """Verifie identifiant + mot de passe. Renvoie l'utilisateur, ou None si KO."""
    user = DEMO_USERS.get(username)
    if user and verify_password(password, user["password_hash"]):
        return {"username": username, "role": user["role"]}
    return None


def create_access_token(username: str, role: str) -> str:
    """Fabrique un jeton JWT signe (contient l'utilisateur, son role, l'expiration)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MIN)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"username": payload.get("sub"), "role": payload.get("role")}
    except JWTError:
        return None


# ════════════════════════════════════════════════════════════════════════
# 4) DEPENDANCES FASTAPI · a brancher sur une route pour exiger un droit
# ════════════════════════════════════════════════════════════════════════
def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict | None:
    """Utilisateur courant ou None (lecture publique autorisée)."""
    if not token:
        return None
    return decode_token(token)


def require_admin(user: dict | None = Depends(get_current_user)) -> dict:
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Jeton requis")
    if user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Rôle administrateur requis")
    return user


# ════════════════════════════════════════════════════════════════════════
# 5) QUOTA · limiteur de debit par IP (protege l'API des abus)
# ════════════════════════════════════════════════════════════════════════
# _hits memorise, pour chaque IP, les horodatages des dernieres requetes.
_hits: dict[str, deque[float]] = defaultdict(deque)


def check_quota(request: Request) -> None:
    """Fenetre glissante par IP : compte les requetes des 60 dernieres secondes.
    Au-dela du quota -> erreur 429 (Too Many Requests). Quota plus large si connecte."""
    ip = request.client.host if request.client else "unknown"
    authed = bool(request.headers.get("authorization"))
    limit = QUOTA_AUTH if authed else QUOTA_ANON

    now = time.monotonic()
    window = _hits[ip]
    while window and now - window[0] > QUOTA_WINDOW_S:
        window.popleft()

    if len(window) >= limit:
        retry = int(QUOTA_WINDOW_S - (now - window[0])) + 1
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota dépassé ({limit} req/min). Authentifiez-vous pour un quota élargi.",
            headers={"Retry-After": str(retry)},
        )
    window.append(now)
