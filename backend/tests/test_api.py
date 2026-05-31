"""Tests de la API (rebanada vertical) con TestClient."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.adapters.api import dependencias as deps
from app.adapters.db.memoria import RepositorioEnMemoria
from app.domain.entities import Bodega
from app.main import crear_app


@pytest.fixture
def client(monkeypatch) -> TestClient:
    repo = RepositorioEnMemoria()
    repo.guardar_bodega(Bodega("BOD-CENTRAL", "Central", "P1"))
    monkeypatch.setattr(deps, "_repositorio", repo)
    monkeypatch.setattr("app.config.settings.settings.cargar_semilla", False)
    monkeypatch.setattr("app.config.settings.settings.ollama_enabled", False)
    app = crear_app()
    with TestClient(app) as c:
        yield c


def _fecha(dias: int) -> str:
    return (date.today() + timedelta(days=dias)).isoformat()


def test_health(client) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_flujo_medicamento_lote_salida_alerta_reporte(client) -> None:
    # Alta de medicamento.
    r = client.post("/medications", json={
        "sku": "MED-PAR-500", "nombre": "Paracetamol 500mg",
        "categoria": "Analgésicos", "stock_minimo": 10,
    })
    assert r.status_code == 201
    mid = r.json()["id"]
    assert r.json()["stock_total"] == 0

    # Entrada de un lote en BOD-CENTRAL.
    r = client.post("/inventory/entries", json={
        "medicamento_id": mid, "numero_lote": "L-1", "bodega_codigo": "BOD-CENTRAL",
        "fecha_caducidad": _fecha(120), "cantidad": 12,
    })
    assert r.status_code == 201
    lote_id = r.json()["lote"]["id"]
    assert r.json()["stock_total_medicamento"] == 12

    # Salida que deja el medicamento bajo mínimo.
    r = client.post("/inventory/exits", json={"lote_id": lote_id, "cantidad": 5})
    assert r.status_code == 201
    assert r.json()["stock_total_medicamento"] == 7
    assert r.json()["bajo_stock"] is True

    # Aparece en alertas de reabastecimiento.
    assert [m["id"] for m in client.get("/alerts/restock").json()] == [mid]

    # Reporte agregado por bodega.
    rep = client.get("/reports/inventory").json()
    assert rep["total_lotes"] == 1
    assert rep["unidades_por_bodega"] == {"BOD-CENTRAL": 7}


def test_alerta_caducidad_por_lote(client) -> None:
    r = client.post("/medications", json={
        "sku": "MED-IBU-400", "nombre": "Ibuprofeno", "categoria": "Antiinflamatorios",
        "stock_minimo": 5,
    })
    mid = r.json()["id"]
    client.post("/inventory/entries", json={
        "medicamento_id": mid, "numero_lote": "L-9", "bodega_codigo": "BOD-CENTRAL",
        "fecha_caducidad": _fecha(10), "cantidad": 20,
    })
    expiring = client.get("/alerts/expiring").json()
    assert [l["numero_lote"] for l in expiring] == ["L-9"]


def test_salida_sin_stock_devuelve_409(client) -> None:
    r = client.post("/medications", json={
        "sku": "MED-X", "nombre": "X", "categoria": "Otros", "stock_minimo": 1,
    })
    mid = r.json()["id"]
    e = client.post("/inventory/entries", json={
        "medicamento_id": mid, "numero_lote": "L-1", "bodega_codigo": "BOD-CENTRAL",
        "fecha_caducidad": _fecha(30), "cantidad": 2,
    })
    lote_id = e.json()["lote"]["id"]
    assert client.post("/inventory/exits", json={"lote_id": lote_id, "cantidad": 9}).status_code == 409


def test_warehouses_y_lots(client) -> None:
    assert [b["codigo"] for b in client.get("/warehouses").json()] == ["BOD-CENTRAL"]
    r = client.post("/medications", json={
        "sku": "MED-Z", "nombre": "Z", "categoria": "Otros", "stock_minimo": 1,
    })
    mid = r.json()["id"]
    client.post("/inventory/entries", json={
        "medicamento_id": mid, "numero_lote": "L-1", "bodega_codigo": "BOD-CENTRAL",
        "fecha_caducidad": _fecha(30), "cantidad": 3,
    })
    lots = client.get("/lots", params={"bodega": "BOD-CENTRAL"}).json()
    assert len(lots) == 1 and lots[0]["bodega_codigo"] == "BOD-CENTRAL"
