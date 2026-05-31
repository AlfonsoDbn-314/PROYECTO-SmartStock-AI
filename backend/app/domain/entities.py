"""Entidades del dominio: Bodega, Medicamento, Lote y Movimiento.

Modelos puros (dataclasses), sin dependencias de frameworks.

Modelo de inventario:
- Un ``Medicamento`` es el catálogo (SKU, nombre, categoría, stock mínimo).
- Un ``Lote`` es una existencia concreta de un medicamento, almacenada en una
  ``Bodega``, con su propio número de lote, fecha de caducidad y stock.
- El stock de un medicamento es la suma del stock de sus lotes.
- Un ``Movimiento`` (entrada/salida) afecta a un lote concreto.
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
class Bodega:
    """Almacén físico donde se guardan los lotes.

    Atributos:
        codigo: Código único de la bodega (p. ej. ``BOD-CENTRAL``).
        nombre: Nombre descriptivo.
        ubicacion: Ubicación o dirección.
    """

    codigo: str
    nombre: str
    ubicacion: str


@dataclass
class Medicamento:
    """Medicamento del catálogo.

    Atributos:
        id: Identificador único.
        sku: Código de referencia (p. ej. ``MED-PAR-500``).
        nombre: Nombre comercial o principio activo.
        categoria: Categoría terapéutica.
        stock_minimo: Umbral por debajo del cual se considera bajo stock.
    """

    id: str
    sku: str
    nombre: str
    categoria: str
    stock_minimo: int

    def __post_init__(self) -> None:
        if self.stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser negativo.")


@dataclass
class Lote:
    """Existencia concreta de un medicamento en una bodega.

    Atributos:
        id: Identificador único del lote.
        medicamento_id: Medicamento al que pertenece.
        numero_lote: Número de lote del fabricante (p. ej. ``L2026-014``).
        bodega_codigo: Bodega donde está almacenado.
        fecha_caducidad: Fecha de caducidad del lote.
        stock_actual: Unidades disponibles de este lote.
    """

    id: str
    medicamento_id: str
    numero_lote: str
    bodega_codigo: str
    fecha_caducidad: date
    stock_actual: int

    def __post_init__(self) -> None:
        if self.stock_actual < 0:
            raise ValueError("El stock del lote no puede ser negativo.")


@dataclass
class Movimiento:
    """Movimiento de inventario sobre un lote.

    Atributos:
        id: Identificador único del movimiento.
        lote_id: Lote afectado.
        tipo: ENTRADA suma stock, SALIDA resta stock.
        cantidad: Unidades movidas (siempre positiva).
        fecha: Momento del movimiento (UTC).
        motivo: Descripción opcional del movimiento.
    """

    id: str
    lote_id: str
    tipo: TipoMovimiento
    cantidad: int
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    motivo: str | None = None

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ValueError("La cantidad del movimiento debe ser mayor que cero.")
