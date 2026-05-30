"""Tests de la regla de negocio de caducidad (dominio puro)."""
from __future__ import annotations

from datetime import date, timedelta

from app.domain.caducidad import (
    esta_caducado,
    medicamentos_caducados,
    medicamentos_proximos_a_caducar,
    proximo_a_caducar,
)
from app.domain.entities import Medicamento

HOY = date(2026, 1, 1)


def _medicamento(sku: str, dias: int) -> Medicamento:
    """Medicamento que caduca dentro de ``dias`` (negativo = ya caducado)."""
    return Medicamento(
        id=sku,
        sku=sku,
        nombre=sku,
        categoria="Analgésicos",
        fecha_caducidad=HOY + timedelta(days=dias),
        stock_actual=10,
        stock_minimo=5,
    )


def test_estados_de_caducidad() -> None:
    caducado = _medicamento("A", -1)
    proximo = _medicamento("B", 10)
    lejano = _medicamento("C", 200)

    assert esta_caducado(caducado, HOY) is True
    assert esta_caducado(proximo, HOY) is False

    assert proximo_a_caducar(proximo, HOY, dias_aviso=30) is True
    assert proximo_a_caducar(lejano, HOY, dias_aviso=30) is False
    # Un caducado NO cuenta como "próximo a caducar".
    assert proximo_a_caducar(caducado, HOY, dias_aviso=30) is False


def test_filtros_y_orden_por_fecha() -> None:
    caducado = _medicamento("A", -5)
    pronto = _medicamento("B", 5)
    despues = _medicamento("C", 20)
    lejano = _medicamento("D", 365)
    lista = [lejano, despues, caducado, pronto]

    assert medicamentos_caducados(lista, HOY) == [caducado]

    proximos = medicamentos_proximos_a_caducar(lista, HOY, dias_aviso=30)
    # Ordenados por fecha de caducidad ascendente, sin incluir el caducado.
    assert [m.sku for m in proximos] == ["B", "C"]
