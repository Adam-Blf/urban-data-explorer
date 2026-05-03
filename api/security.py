"""Auth JWT · login démo + dépendance `get_current_user`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from pipeline.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_credentials(username: str, password: str) -> bool:
    """Compare avec les credentials démo (en prod, lecture en base)."""
    s = get_settings()
    return username == s.demo_user and password == s.demo_password


def create_access_token(subject: str, ttl_minutes: int | None = None) -> str:
    s = get_settings()
    expire = datetime.now(UTC) + timedelta(
        minutes=ttl_minutes or s.jwt_ttl_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> str:
    s = get_settings()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="invalid token (no sub)")
    return sub
