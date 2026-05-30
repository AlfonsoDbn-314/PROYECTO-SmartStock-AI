"""Tests de la API (rebanada vertical) con TestClient."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.api import dependencias as deps
from app.adapters.db.memoria import RepositorioEnMemoria
from app.main import crear_app


@pytest.fixture
def client(monkeypatch) -> TestClient:
    # Repositorio limpio por test, sin semilla, para aislar el escenario.
    repo = RepositorioEnMemoria()
    monkeypatch.setattr(deps, "_repositorio", repo)
    monkeypatch.setattr("app.config.settings.settings.cargar_semilla", False)
    app = crear_app()
    with TestClient(app) as c:
        yield c


def test_health(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_flujo_medicamento_movimiento_alerta_reporte(client) -> None:
    # Crear medicamento cerca del mínimo.
    r = client.post("/medications", json={
        "sku": "MED-PAR-500", "nombre": "Paracetamol 500mg",
        "categoria": "Analgésicos", "fecha_caducidad": "2027-06-30",
        "stock_inicial": 6, "stock_minimo": 5,
    })
    assert r.status_code == 201
    medicamento_id = r.json()["id"]
    assert r.json()["bajo_stock"] is False
    assert r.json()["fecha_caducidad"] == "2027-06-30"

    # Registrar una salida que dispara la alerta.
    r = client.post("/inventory/movements", json={
        "medicamento_id": medicamento_id, "tipo": "salida", "cantidad": 2,
    })
    assert r.status_code == 201
    assert r.json()["medicamento"]["stock_actual"] == 4
    assert r.json()["bajo_stock"] is True

    # Aparece en alertas de reabastecimiento.
    r = client.get("/alerts/restock")
    assert [m["id"] for m in r.json()] == [medicamento_id]

    # Y en el reporte agregado (sin precios, con unidades por categoría).
    r = client.get("/reports/inventory")
    data = r.json()
    assert data["total_medicamentos"] == 1
    assert data["total_unidades"] == 4
    assert data["unidades_por_categoria"] == {"Analgésicos": 4}
    assert [m["sku"] for m in data["medicamentos_en_riesgo"]] == ["MED-PAR-500"]


def test_alerta_caducidad(client) -> None:
    from datetime import date, timedelta

    pronto = (date.today() + timedelta(days=10)).isoformat()
    client.post("/medications", json={
        "sku": "MED-IBU-400", "nombre": "Ibuprofeno 400mg",
        "categoria": "Antiinflamatorios", "fecha_caducidad": pronto,
        "stock_inicial": 20, "stock_minimo": 5,
    })
    r = client.get("/alerts/expiring")
    assert [m["sku"] for m in r.json()] == ["MED-IBU-400"]


def test_salida_sin_stock_devuelve_409(client) -> None:
    r = client.post("/medications", json={
        "sku": "MED-X", "nombre": "X", "categoria": "Otros",
        "fecha_caducidad": "2027-01-01", "stock_inicial": 1, "stock_minimo": 1,
    })
    medicamento_id = r.json()["id"]

    r = client.post("/inventory/movements", json={
        "medicamento_id": medicamento_id, "tipo": "salida", "cantidad": 5,
    })
    assert r.status_code == 409


def test_sku_duplicado_devuelve_409(client) -> None:
    payload = {
        "sku": "MED-DUP", "nombre": "Dup", "categoria": "Otros",
        "fecha_caducidad": "2027-01-01", "stock_inicial": 1, "stock_minimo": 1,
    }
    assert client.post("/medications", json=payload).status_code == 201
    assert client.post("/medications", json=payload).status_code == 409
