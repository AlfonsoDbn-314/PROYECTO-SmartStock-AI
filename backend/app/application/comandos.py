"""Comandos de entrada de los casos de uso (DTOs internos).

Son objetos simples (sin Pydantic) para no acoplar la aplicación a la API.
Los schemas de Pydantic viven en la capa de adaptadores.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.entities import TipoMovimiento


@dataclass
class CrearMedicamentoCmd:
    sku: str
    nombre: str
    categoria: str
    fecha_caducidad: date
    stock_inicial: int
    stock_minimo: int


@dataclass
class RegistrarMovimientoCmd:
    medicamento_id: str
    tipo: TipoMovimiento
    cantidad: int
    motivo: str | None = None
