"""Tests de los casos de uso (application) con el repositorio en memoria."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.adapters.db.memoria import RepositorioEnMemoria
from app.application.comandos import (
    CrearMedicamentoCmd,
    RegistrarEntradaCmd,
    RegistrarSalidaCmd,
)
from app.application.consultas import (
    GenerarReporteInventario,
    ListarAlertasReabastecimiento,
    ListarLotes,
    ListarMedicamentos,
)
from app.application.crear_medicamento import CrearMedicamento, SkuDuplicadoError
from app.application.movimientos import RegistrarEntrada, RegistrarSalida
from app.domain.entities import Bodega
from app.domain.errors import (
    BodegaNoEncontradaError,
    LoteNoEncontradoError,
    StockInsuficienteError,
)

HOY = date.today()


@pytest.fixture
def repo() -> RepositorioEnMemoria:
    r = RepositorioEnMemoria()
    r.guardar_bodega(Bodega("BOD-CENTRAL", "Central", "P1"))
    return r


def _crear_med(repo, sku="MED-PAR-500", stock_minimo=10) -> str:
    m = CrearMedicamento(repo).ejecutar(
        CrearMedicamentoCmd(sku, f"Med {sku}", "Analgésicos", stock_minimo)
    )
    return m.id


def test_crear_medicamento_y_sku_duplicado(repo) -> None:
    _crear_med(repo)
    assert len(ListarMedicamentos(repo).ejecutar()) == 1
    with pytest.raises(SkuDuplicadoError):
        _crear_med(repo)


def test_entrada_crea_lote_y_repone(repo) -> None:
    mid = _crear_med(repo, stock_minimo=10)
    entrada = RegistrarEntrada(repo)

    r1 = entrada.ejecutar(
        RegistrarEntradaCmd(mid, "L-1", "BOD-CENTRAL", HOY + timedelta(days=100), 6)
    )
    assert r1.stock_total == 6
    assert r1.bajo_stock is True  # 6 < 10

    # Misma combinación lote+bodega: repone el mismo lote (no crea otro).
    r2 = entrada.ejecutar(
        RegistrarEntradaCmd(mid, "L-1", "BOD-CENTRAL", HOY + timedelta(days=100), 5)
    )
    assert r2.stock_total == 11
    assert r2.bajo_stock is False
    assert len(ListarLotes(repo).ejecutar()) == 1


def test_entrada_en_bodega_inexistente_falla(repo) -> None:
    mid = _crear_med(repo)
    with pytest.raises(BodegaNoEncontradaError):
        RegistrarEntrada(repo).ejecutar(
            RegistrarEntradaCmd(mid, "L-1", "BOD-XXX", HOY + timedelta(days=30), 5)
        )


def test_salida_descuenta_y_valida_stock(repo) -> None:
    mid = _crear_med(repo, stock_minimo=5)
    entrada = RegistrarEntrada(repo).ejecutar(
        RegistrarEntradaCmd(mid, "L-1", "BOD-CENTRAL", HOY + timedelta(days=100), 8)
    )
    lote_id = entrada.lote.id

    salida = RegistrarSalida(repo)
    r = salida.ejecutar(RegistrarSalidaCmd(lote_id, 5))
    assert r.lote.stock_actual == 3
    assert r.stock_total == 3
    assert r.bajo_stock is True

    with pytest.raises(StockInsuficienteError):
        salida.ejecutar(RegistrarSalidaCmd(lote_id, 99))
    with pytest.raises(LoteNoEncontradoError):
        salida.ejecutar(RegistrarSalidaCmd("inexistente", 1))


def test_reporte_agrega_lotes_bodegas_y_caducidad(repo) -> None:
    repo.guardar_bodega(Bodega("BOD-SUR", "Sur", "P2"))
    mid = _crear_med(repo, sku="MED-PAR-500", stock_minimo=20)
    entrada = RegistrarEntrada(repo)
    entrada.ejecutar(RegistrarEntradaCmd(mid, "L-1", "BOD-CENTRAL", HOY + timedelta(days=300), 10))
    entrada.ejecutar(RegistrarEntradaCmd(mid, "L-2", "BOD-SUR", HOY + timedelta(days=10), 5))

    reporte = GenerarReporteInventario(repo).ejecutar(hoy=HOY)
    assert reporte.total_medicamentos == 1
    assert reporte.total_lotes == 2
    assert reporte.total_unidades == 15
    assert reporte.unidades_por_bodega == {"BOD-CENTRAL": 10, "BOD-SUR": 5}
    assert [r.medicamento.sku for r in reporte.medicamentos_en_riesgo] == ["MED-PAR-500"]
    assert [l.numero_lote for l in reporte.lotes_proximos_a_caducar] == ["L-2"]


def test_alertas_reabastecimiento(repo) -> None:
    mid = _crear_med(repo, stock_minimo=10)
    RegistrarEntrada(repo).ejecutar(
        RegistrarEntradaCmd(mid, "L-1", "BOD-CENTRAL", HOY + timedelta(days=100), 4)
    )
    alertas = ListarAlertasReabastecimiento(repo).ejecutar()
    assert [v.medicamento.id for v in alertas] == [mid]
