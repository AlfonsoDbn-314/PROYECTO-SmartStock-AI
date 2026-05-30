"""Punto de entrada de la API FastAPI (composition root del proceso)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.api import dependencias as deps
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
    app.include_router(router)
    return app


app = crear_app()
