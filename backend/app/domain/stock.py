"""Reglas de negocio puras sobre el stock.

El stock de un medicamento es la suma del stock de sus lotes. Los movimientos
afectan a un lote concreto. Funciones sin estado ni infraestructura.
"""
from __future__ import annotations

from .entities import Lote, Medicamento, Movimiento, TipoMovimiento
from .errors import StockInsuficienteError


def calcular_stock_tras_movimiento(stock_actual: int, movimiento: Movimiento) -> int:
    """Calcula el nuevo stock de un lote tras aplicar un movimiento.

    - ENTRADA suma la cantidad.
    - SALIDA resta la cantidad; si no hay suficiente, lanza
      ``StockInsuficienteError`` (no se permiten stocks negativos).
    """
    if movimiento.tipo is TipoMovimiento.ENTRADA:
        return stock_actual + movimiento.cantidad

    # SALIDA
    if movimiento.cantidad > stock_actual:
        raise StockInsuficienteError(stock_actual, movimiento.cantidad)
    return stock_actual - movimiento.cantidad


def aplicar_movimiento(lote: Lote, movimiento: Movimiento) -> Lote:
    """Aplica un movimiento al lote y devuelve el lote con stock recalculado."""
    lote.stock_actual = calcular_stock_tras_movimiento(lote.stock_actual, movimiento)
    return lote


def stock_total(lotes: list[Lote]) -> int:
    """Suma de unidades de una colección de lotes."""
    return sum(lote.stock_actual for lote in lotes)


def esta_en_bajo_stock(medicamento: Medicamento, lotes: list[Lote]) -> bool:
    """El stock total de los lotes del medicamento está por debajo del mínimo."""
    return stock_total(lotes) < medicamento.stock_minimo
