from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..security import authenticate, create_access_token, require_admin

# Toutes les routes de ce fichier commencent par /auth (ex : /auth/token).
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Connexion : on envoie username + password, on recoit un jeton JWT.
    Comptes de demo : demo/demo (lecture) ou admin/admin (administration)."""
    user = authenticate(form.username, form.password)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


@router.get("/me")
def me(user: dict = Depends(require_admin)):
    """Route protégée de démonstration (rôle admin requis)."""
    return {"authenticated": True, **user}
