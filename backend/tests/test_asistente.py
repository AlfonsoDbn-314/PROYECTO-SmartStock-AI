"""Tests del asistente RAG en modo local."""
from __future__ import annotations

from app.adapters.rag.local import AsistenteLocal


def _vault(tmp_path):
    (tmp_path / "reglas.md").write_text(
        "# Reabastecimiento\n\n"
        "Un medicamento entra en bajo stock cuando el stock actual es menor que el "
        "stock minimo y debe generar una alerta de reabastecimiento.\n\n"
        "# Caducidad\n\n"
        "Un medicamento proximo a caducar debe priorizarse o retirarse del stock.",
        encoding="utf-8",
    )
    return tmp_path


def test_ingesta_indexa_fragmentos(tmp_path) -> None:
    asistente = AsistenteLocal(_vault(tmp_path))
    assert asistente.ingerir() >= 2


def test_consulta_recupera_contexto_relevante(tmp_path) -> None:
    asistente = AsistenteLocal(_vault(tmp_path))
    r = asistente.consultar("¿Cuándo se genera una alerta de reabastecimiento?")
    assert r.modo == "local"
    assert "reabastecimiento" in r.respuesta.lower()
    assert "reglas.md" in r.fuentes


def test_consulta_sin_coincidencias(tmp_path) -> None:
    asistente = AsistenteLocal(_vault(tmp_path))
    r = asistente.consultar("xyzzy plugh")
    assert r.fuentes == []


def test_pregunta_de_caducidad_usa_inventario_en_vivo(tmp_path) -> None:
    from datetime import date, timedelta
    from app.domain.entities import Medicamento

    hoy = date.today()
    meds = [
        Medicamento("1", "MED-A", "Med A", "Cat", hoy + timedelta(days=200), 10, 5),
        Medicamento("2", "MED-B", "Med B", "Cat", hoy + timedelta(days=12), 10, 5),
    ]
    asistente = AsistenteLocal(_vault(tmp_path), proveedor_inventario=lambda: meds)

    # "vencerse" debe mapearse a caducidad y responder desde el inventario.
    r = asistente.consultar("¿cuál es el próximo lote por vencerse?")
    assert r.fuentes == ["inventario"]
    assert "MED-B" in r.respuesta


def test_pregunta_de_stock_usa_inventario_en_vivo(tmp_path) -> None:
    from datetime import date, timedelta
    from app.domain.entities import Medicamento

    hoy = date.today()
    meds = [
        Medicamento("1", "MED-A", "Med A", "Cat", hoy + timedelta(days=200), 2, 5),
    ]
    asistente = AsistenteLocal(_vault(tmp_path), proveedor_inventario=lambda: meds)
    r = asistente.consultar("¿qué debo reabastecer?")
    assert r.fuentes == ["inventario"]
    assert "MED-A" in r.respuesta


def test_disponibilidad_por_nombre(tmp_path) -> None:
    from datetime import date, timedelta
    from app.domain.entities import Medicamento

    hoy = date.today()
    meds = [
        Medicamento("1", "MED-PAR-500", "Paracetamol 500mg", "Analgésicos",
                    hoy + timedelta(days=200), 8, 5),
    ]
    asistente = AsistenteLocal(_vault(tmp_path), proveedor_inventario=lambda: meds)

    si = asistente.consultar("¿tenemos paracetamol?")
    assert si.fuentes == ["inventario"]
    assert "Paracetamol" in si.respuesta

    no = asistente.consultar("¿tenemos dexketoprofeno?")
    assert no.fuentes == ["inventario"]
    assert "No" in no.respuesta and "dexketoprofeno" in no.respuesta
