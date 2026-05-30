"""Tests de los casos de uso (application) con el repositorio en memoria."""
from __future__ import annotations

import itertools
from datetime import date

import pytest

from app.adapters.db.memoria import RepositorioEnMemoria
from app.application.comandos import CrearMedicamentoCmd, RegistrarMovimientoCmd
from app.application.consultas import (
    GenerarReporteInventario,
    ListarAlertasReabastecimiento,
    ListarMedicamentos,
)
from app.application.crear_medicamento import CrearMedicamento, SkuDuplicadoError
from app.application.registrar_movimiento import RegistrarMovimiento
from app.domain.entities import TipoMovimiento
from app.domain.errors import MedicamentoNoEncontradoError, StockInsuficienteError

HOY = date(2026, 1, 1)


@pytest.fixture
def repo() -> RepositorioEnMemoria:
    return RepositorioEnMemoria()


@pytest.fixture
def ids():
    """Fábrica de IDs determinista y compartida durante el test."""
    contador = itertools.count(1)
    return lambda: f"id-{next(contador)}"


def _crear(repo, ids, **kwargs):
    base = dict(
        sku="MED-PAR-500",
        nombre="Paracetamol 500mg",
        categoria="Analgésicos",
        fecha_caducidad=date(2027, 1, 1),
        stock_inicial=10,
        stock_minimo=5,
    )
    base.update(kwargs)
    return CrearMedicamento(repo, id_factory=ids).ejecutar(CrearMedicamentoCmd(**base))


def test_crear_medicamento_y_sku_duplicado(repo, ids) -> None:
    medicamento = _crear(repo, ids)
    assert medicamento.id == "id-1"
    assert ListarMedicamentos(repo).ejecutar() == [medicamento]

    with pytest.raises(SkuDuplicadoError):
        _crear(repo, ids)  # mismo SKU


def test_registrar_salida_recalcula_stock_y_dispara_alerta(repo, ids) -> None:
    medicamento = _crear(repo, ids, stock_inicial=6, stock_minimo=5)

    caso = RegistrarMovimiento(repo, id_factory=ids)
    resultado = caso.ejecutar(
        RegistrarMovimientoCmd(medicamento.id, TipoMovimiento.SALIDA, 2)
    )

    assert resultado.medicamento.stock_actual == 4
    assert resultado.bajo_stock is True

    alertas = ListarAlertasReabastecimiento(repo).ejecutar()
    assert [m.id for m in alertas] == [medicamento.id]


def test_movimiento_invalido_lanza_errores(repo, ids) -> None:
    medicamento = _crear(repo, ids, stock_inicial=3)
    caso = RegistrarMovimiento(repo, id_factory=ids)

    with pytest.raises(StockInsuficienteError):
        caso.ejecutar(RegistrarMovimientoCmd(medicamento.id, TipoMovimiento.SALIDA, 4))

    with pytest.raises(MedicamentoNoEncontradoError):
        caso.ejecutar(RegistrarMovimientoCmd("inexistente", TipoMovimiento.ENTRADA, 1))


def test_reporte_agrega_unidades_riesgo_y_caducidad(repo, ids) -> None:
    from datetime import timedelta

    _crear(repo, ids, sku="MED-PAR-500", categoria="Analgésicos",
           fecha_caducidad=HOY + timedelta(days=300), stock_inicial=10, stock_minimo=5)
    _crear(repo, ids, sku="MED-IBU-400", categoria="Antiinflamatorios",
           fecha_caducidad=HOY + timedelta(days=10), stock_inicial=1, stock_minimo=5)

    reporte = GenerarReporteInventario(repo).ejecutar(hoy=HOY)

    assert reporte.total_medicamentos == 2
    assert reporte.total_unidades == 11
    assert reporte.unidades_por_categoria == {
        "Analgésicos": 10, "Antiinflamatorios": 1,
    }
    assert [m.sku for m in reporte.medicamentos_en_riesgo] == ["MED-IBU-400"]
    assert [m.sku for m in reporte.proximos_a_caducar] == ["MED-IBU-400"]
    assert reporte.caducados == []
