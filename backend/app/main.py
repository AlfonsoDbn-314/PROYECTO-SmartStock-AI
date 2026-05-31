"""Punto de entrada de la API FastAPI (composition root del proceso)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.adapters.api import dependencias as deps
from app.adapters.api.auth import public_router, requerir_usuario
from app.adapters.api.errores import registrar_manejadores_de_error
from app.adapters.api.rutas import router
from app.adapters.db.semilla import cargar_semilla
from app.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.cargar_semilla:
        cargar_semilla(deps.obtener_repositorio())
    yield


def crear_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    registrar_manejadores_de_error(app)
    # Rutas públicas: /health, /auth/login, /auth/me.
    app.include_router(public_router)
    # Resto de la API protegida con token Bearer.
    app.include_router(router, dependencies=[Depends(requerir_usuario)])
    return app


app = crear_app()
