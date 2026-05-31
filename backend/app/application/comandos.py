"""Comandos de entrada de los casos de uso (DTOs internos).

Son objetos simples (sin Pydantic) para no acoplar la aplicación a la API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class CrearMedicamentoCmd:
    sku: str
    nombre: str
    categoria: str
    stock_minimo: int


@dataclass
class RegistrarEntradaCmd:
    """Entrada de stock: crea (o repone) un lote en una bodega."""

    medicamento_id: str
    numero_lote: str
    bodega_codigo: str
    fecha_caducidad: date
    cantidad: int
    motivo: str | None = None


@dataclass
class RegistrarSalidaCmd:
    """Salida de stock desde un lote concreto."""

    lote_id: str
    cantidad: int
    motivo: str | None = None
