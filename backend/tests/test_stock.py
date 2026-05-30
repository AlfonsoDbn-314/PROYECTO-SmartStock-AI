"""Tests de la regla de negocio de stock (dominio puro, sin API ni BD)."""
from __future__ import annotations

from datetime import date

import pytest

from app.domain.entities import Medicamento, Movimiento, TipoMovimiento
from app.domain.errors import StockInsuficienteError
from app.domain.stock import (
    aplicar_movimiento,
    calcular_stock_tras_movimiento,
    esta_en_bajo_stock,
    medicamentos_en_riesgo,
)


def _medicamento(stock_actual: int = 10, stock_minimo: int = 5) -> Medicamento:
    return Medicamento(
        id="m1",
        sku="MED-PAR-500",
        nombre="Paracetamol 500mg",
        categoria="Analgésicos",
        fecha_caducidad=date(2027, 1, 1),
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
    )


def _movimiento(tipo: TipoMovimiento, cantidad: int) -> Movimiento:
    return Movimiento(id="mov1", medicamento_id="m1", tipo=tipo, cantidad=cantidad)


def test_recalculo_entrada_y_salida_actualiza_stock() -> None:
    """Una entrada suma y una salida resta del stock actual."""
    medicamento = _medicamento(stock_actual=10)

    aplicar_movimiento(medicamento, _movimiento(TipoMovimiento.ENTRADA, 5))
    assert medicamento.stock_actual == 15

    aplicar_movimiento(medicamento, _movimiento(TipoMovimiento.SALIDA, 8))
    assert medicamento.stock_actual == 7


def test_salida_mayor_que_stock_lanza_error_y_no_deja_negativo() -> None:
    """No se permite retirar más de lo disponible (sin stocks negativos)."""
    medicamento = _medicamento(stock_actual=3)

    with pytest.raises(StockInsuficienteError):
        calcular_stock_tras_movimiento(
            medicamento.stock_actual, _movimiento(TipoMovimiento.SALIDA, 4)
        )

    # El stock no se modificó al fallar la regla.
    assert medicamento.stock_actual == 3


def test_deteccion_de_bajo_stock_y_medicamentos_en_riesgo() -> None:
    """Bajo stock cuando stock_actual < stock_minimo; se filtran los en riesgo."""
    sano = _medicamento(stock_actual=10, stock_minimo=5)
    en_riesgo = _medicamento(stock_actual=2, stock_minimo=5)

    assert esta_en_bajo_stock(sano) is False
    assert esta_en_bajo_stock(en_riesgo) is True

    # En el límite (igual al mínimo) todavía NO es bajo stock.
    en_limite = _medicamento(stock_actual=5, stock_minimo=5)
    assert esta_en_bajo_stock(en_limite) is False

    riesgo = medicamentos_en_riesgo([sano, en_riesgo, en_limite])
    assert riesgo == [en_riesgo]
