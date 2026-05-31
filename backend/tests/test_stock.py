"""Tests de la regla de negocio de stock por lote (dominio puro)."""
from __future__ import annotations

from datetime import date

import pytest

from app.domain.entities import Lote, Medicamento, Movimiento, TipoMovimiento
from app.domain.errors import StockInsuficienteError
from app.domain.stock import (
    aplicar_movimiento,
    calcular_stock_tras_movimiento,
    esta_en_bajo_stock,
    stock_total,
)


def _med(stock_minimo: int = 10) -> Medicamento:
    return Medicamento("m1", "MED-PAR-500", "Paracetamol", "Analgésicos", stock_minimo)


def _lote(stock: int, mid: str = "m1") -> Lote:
    return Lote("l", mid, "L-1", "BOD-CENTRAL", date(2027, 1, 1), stock)


def _mov(tipo: TipoMovimiento, cantidad: int) -> Movimiento:
    return Movimiento("mov", "l", tipo, cantidad)


def test_recalculo_entrada_y_salida_en_lote() -> None:
    lote = _lote(10)
    aplicar_movimiento(lote, _mov(TipoMovimiento.ENTRADA, 5))
    assert lote.stock_actual == 15
    aplicar_movimiento(lote, _mov(TipoMovimiento.SALIDA, 8))
    assert lote.stock_actual == 7


def test_salida_mayor_que_stock_lanza_error() -> None:
    lote = _lote(3)
    with pytest.raises(StockInsuficienteError):
        calcular_stock_tras_movimiento(lote.stock_actual, _mov(TipoMovimiento.SALIDA, 4))
    assert lote.stock_actual == 3


def test_stock_total_y_bajo_stock_suma_lotes() -> None:
    med = _med(stock_minimo=10)
    lotes = [_lote(4), _lote(3)]
    assert stock_total(lotes) == 7
    assert esta_en_bajo_stock(med, lotes) is True  # 7 < 10

    lotes.append(_lote(5))
    assert stock_total(lotes) == 12
    assert esta_en_bajo_stock(med, lotes) is False  # 12 >= 10
