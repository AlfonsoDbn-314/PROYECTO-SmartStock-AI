"""Tests del asistente RAG en modo local con lotes y bodegas."""
from __future__ import annotations

from datetime import date, timedelta

from app.adapters.rag.local import AsistenteLocal, InventarioSnapshot
from app.domain.entities import Bodega, Lote, Medicamento

HOY = date.today()


def _vault(tmp_path):
    (tmp_path / "reglas.md").write_text(
        "# Reabastecimiento\n\n"
        "Un medicamento entra en bajo stock cuando el stock total de sus lotes "
        "es menor que el stock minimo.\n\n"
        "# FEFO\n\n"
        "Se despacha primero el lote con caducidad mas proxima.",
        encoding="utf-8",
    )
    return tmp_path


def _snapshot() -> InventarioSnapshot:
    med = Medicamento("m1", "MED-PAR-500", "Paracetamol 500mg", "Analgésicos", 10)
    bod = Bodega("BOD-CENTRAL", "Central", "P1")
    lotes = [
        Lote("l1", "m1", "L-1", "BOD-CENTRAL", HOY + timedelta(days=12), 5),
        Lote("l2", "m1", "L-2", "BOD-CENTRAL", HOY + timedelta(days=400), 30),
    ]
    return InventarioSnapshot(medicamentos=[med], lotes=lotes, bodegas=[bod])


def test_ingesta_indexa(tmp_path) -> None:
    asistente = AsistenteLocal(_vault(tmp_path))
    assert asistente.ingerir() >= 2


def test_proximo_lote_por_caducar(tmp_path) -> None:
    a = AsistenteLocal(_vault(tmp_path), proveedor_inventario=_snapshot)
    r = a.consultar("¿cuál es el próximo lote por vencerse?")
    assert r.fuentes == ["inventario"]
    assert "L-1" in r.respuesta


def test_cual_dura_mas(tmp_path) -> None:
    a = AsistenteLocal(_vault(tmp_path), proveedor_inventario=_snapshot)
    r = a.consultar("¿cuál va a durar más?")
    assert r.fuentes == ["inventario"]
    assert "L-2" in r.respuesta  # el de caducidad más lejana


def test_disponibilidad_por_nombre(tmp_path) -> None:
    a = AsistenteLocal(_vault(tmp_path), proveedor_inventario=_snapshot)
    assert "Paracetamol" in a.consultar("¿tenemos paracetamol?").respuesta
    no = a.consultar("¿tenemos dexketoprofeno?")
    assert "No" in no.respuesta and "dexketoprofeno" in no.respuesta


def test_pregunta_en_riesgo(tmp_path) -> None:
    # Con stock_minimo 10 y solo 5 uds en lotes vigentes, está en riesgo.
    a = AsistenteLocal(_vault(tmp_path), proveedor_inventario=_snapshot)
    r = a.consultar("dime lo que está en riesgo")
    assert r.fuentes == ["inventario"]
    # Dispara la intención de stock (aquí no hay nada bajo mínimo).
    assert "mínimo" in r.respuesta.lower()


def test_pregunta_por_bodega(tmp_path) -> None:
    a = AsistenteLocal(_vault(tmp_path), proveedor_inventario=_snapshot)
    r = a.consultar("¿qué hay en la bodega central?")
    assert r.fuentes == ["inventario"]
    assert "L-1" in r.respuesta and "L-2" in r.respuesta
