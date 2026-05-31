"""Traducción de errores de dominio a respuestas HTTP."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.crear_medicamento import SkuDuplicadoError
from app.domain.errors import (
    BodegaNoEncontradaError,
    ErrorDeDominio,
    LoteNoEncontradoError,
    MedicamentoNoEncontradoError,
    StockInsuficienteError,
)


def registrar_manejadores_de_error(app: FastAPI) -> None:
    @app.exception_handler(MedicamentoNoEncontradoError)
    async def _med_no(_: Request, exc: MedicamentoNoEncontradoError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(LoteNoEncontradoError)
    async def _lote_no(_: Request, exc: LoteNoEncontradoError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(BodegaNoEncontradaError)
    async def _bod_no(_: Request, exc: BodegaNoEncontradaError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(StockInsuficienteError)
    async def _stock(_: Request, exc: StockInsuficienteError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(SkuDuplicadoError)
    async def _sku(_: Request, exc: SkuDuplicadoError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ErrorDeDominio)
    async def _dominio(_: Request, exc: ErrorDeDominio):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
