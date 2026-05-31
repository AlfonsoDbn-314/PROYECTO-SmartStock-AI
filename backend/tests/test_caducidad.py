"""Tests de la regla de negocio de caducidad por lote (dominio puro)."""
from __future__ import annotations

from datetime import date, timedelta

from app.domain.caducidad import (
    esta_caducado,
    lotes_caducados,
    lotes_proximos_a_caducar,
    proximo_a_caducar,
)
from app.domain.entities import Lote

HOY = date(2026, 1, 1)


def _lote(numero: str, dias: int) -> Lote:
    return Lote(numero, "m1", numero, "BOD-CENTRAL", HOY + timedelta(days=dias), 10)


def test_estados_de_caducidad() -> None:
    caducado = _lote("A", -1)
    proximo = _lote("B", 10)
    lejano = _lote("C", 200)

    assert esta_caducado(caducado, HOY) is True
    assert esta_caducado(proximo, HOY) is False
    assert proximo_a_caducar(proximo, HOY, 30) is True
    assert proximo_a_caducar(lejano, HOY, 30) is False
    assert proximo_a_caducar(caducado, HOY, 30) is False


def test_filtros_y_orden_fefo() -> None:
    caducado = _lote("A", -5)
    pronto = _lote("B", 5)
    despues = _lote("C", 20)
    lejano = _lote("D", 365)
    lista = [lejano, despues, caducado, pronto]

    assert [l.numero_lote for l in lotes_caducados(lista, HOY)] == ["A"]
    proximos = lotes_proximos_a_caducar(lista, HOY, 30)
    assert [l.numero_lote for l in proximos] == ["B", "C"]  # FEFO
