"""Login sencillo: token Bearer firmado con HMAC (sin dependencias externas).

Expone las rutas públicas (`/health`, `/auth/login`) y la dependencia
``requerir_usuario`` que protege el resto de la API.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import time

from fastapi import APIRouter, Header, HTTPException

from app.config.settings import settings

from .schemas import LoginIn, SaludOut, TokenOut, UsuarioOut

public_router = APIRouter()


def _firmar(payload: str) -> str:
    return hmac.new(
        settings.auth_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def crear_token(username: str) -> str:
    """Genera un token opaco firmado: base64(usuario:exp:firma)."""
    exp = int(time.time()) + settings.auth_token_ttl
    payload = f"{username}:{exp}"
    bruto = f"{payload}:{_firmar(payload)}"
    return base64.urlsafe_b64encode(bruto.encode()).decode()


def verificar_token(token: str) -> str | None:
    """Devuelve el usuario si el token es válido y no ha expirado; si no, None."""
    try:
        bruto = base64.urlsafe_b64decode(token.encode()).decode()
        username, exp, firma = bruto.rsplit(":", 2)
    except Exception:
        return None
    payload = f"{username}:{exp}"
    if not hmac.compare_digest(firma, _firmar(payload)):
        return None
    if int(exp) < int(time.time()):
        return None
    return username


def requerir_usuario(authorization: str | None = Header(default=None)) -> str:
    """Dependencia que exige un token Bearer válido (si la auth está activa)."""
    if not settings.auth_enabled:
        return "anonimo"
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="No autenticado.")
    usuario = verificar_token(authorization.split(" ", 1)[1])
    if usuario is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    return usuario


@public_router.get("/health", response_model=SaludOut, tags=["salud"])
def health() -> SaludOut:
    return SaludOut(status="ok")


@public_router.post("/auth/login", response_model=TokenOut, tags=["auth"])
def login(body: LoginIn) -> TokenOut:
    if (
        body.username != settings.auth_username
        or body.password != settings.auth_password
    ):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    return TokenOut(
        access_token=crear_token(body.username),
        expires_in=settings.auth_token_ttl,
    )


@public_router.get("/auth/me", response_model=UsuarioOut, tags=["auth"])
def me(authorization: str | None = Header(default=None)) -> UsuarioOut:
    return UsuarioOut(username=requerir_usuario(authorization))
