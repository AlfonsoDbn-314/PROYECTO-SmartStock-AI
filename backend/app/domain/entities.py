"""Entidades del dominio: Medicamento y Movimiento.

Modelos puros (dataclasses), sin dependencias de frameworks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class TipoMovimiento(str, Enum):
    """Tipo de movimiento de inventario."""

    ENTRADA = "entrada"
    SALIDA = "salida"


@dataclass
class Medicamento:
    """Medicamento del inventario.

    Atributos:
        id: Identificador único del medicamento.
        sku: Código de referencia (p. ej. ``MED-PAR-500``).
        nombre: Nombre comercial o principio activo.
        categoria: Categoría terapéutica (Analgésicos, Antibióticos, ...).
        fecha_caducidad: Fecha de caducidad del lote.
        stock_actual: Unidades disponibles en este momento.
        stock_minimo: Umbral por debajo del cual se considera bajo stock.
    """

    id: str
    sku: str
    nombre: str
    categoria: str
    fecha_caducidad: date
    stock_actual: int
    stock_minimo: int

    def __post_init__(self) -> None:
        if self.stock_actual < 0:
            raise ValueError("El stock actual no puede ser negativo.")
        if self.stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser negativo.")


@dataclass
class Movimiento:
    """Movimiento de inventario sobre un medicamento.

    Atributos:
        id: Identificador único del movimiento.
        medicamento_id: Medicamento afectado.
        tipo: ENTRADA suma stock, SALIDA resta stock.
        cantidad: Unidades movidas (siempre positiva).
        fecha: Momento del movimiento (UTC).
        motivo: Descripción opcional del movimiento.
    """

    id: str
    medicamento_id: str
    tipo: TipoMovimiento
    cantidad: int
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    motivo: str | None = None

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ValueError("La cantidad del movimiento debe ser mayor que cero.")
