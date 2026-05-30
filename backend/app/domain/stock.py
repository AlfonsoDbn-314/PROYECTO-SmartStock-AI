"""Reglas de negocio puras sobre el stock.

Funciones sin estado ni dependencias de infraestructura: reciben entidades
y devuelven resultados. Se pueden probar sin API ni base de datos.
"""
from __future__ import annotations

from .entities import Medicamento, Movimiento, TipoMovimiento
from .errors import StockInsuficienteError


def calcular_stock_tras_movimiento(stock_actual: int, movimiento: Movimiento) -> int:
    """Calcula el nuevo stock tras aplicar un movimiento.

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


def aplicar_movimiento(medicamento: Medicamento, movimiento: Movimiento) -> Medicamento:
    """Aplica un movimiento al medicamento y devuelve el medicamento con stock recalculado.

    Muta ``stock_actual`` del medicamento recibido y lo devuelve por conveniencia.
    """
    medicamento.stock_actual = calcular_stock_tras_movimiento(
        medicamento.stock_actual, movimiento
    )
    return medicamento


def esta_en_bajo_stock(medicamento: Medicamento) -> bool:
    """Indica si el medicamento está en bajo stock.

    Regla de reabastecimiento: el stock actual está por debajo del mínimo.
    """
    return medicamento.stock_actual < medicamento.stock_minimo


def medicamentos_en_riesgo(medicamentos: list[Medicamento]) -> list[Medicamento]:
    """Filtra los medicamentos que necesitan reabastecimiento."""
    return [m for m in medicamentos if esta_en_bajo_stock(m)]
