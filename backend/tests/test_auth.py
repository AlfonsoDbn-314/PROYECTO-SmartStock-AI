"""Tests del login sencillo y la protección de rutas."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import crear_app


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setattr("app.config.settings.settings.cargar_semilla", False)
    monkeypatch.setattr("app.config.settings.settings.ollama_enabled", False)
    monkeypatch.setattr("app.config.settings.settings.auth_enabled", True)
    monkeypatch.setattr("app.config.settings.settings.auth_username", "admin")
    monkeypatch.setattr("app.config.settings.settings.auth_password", "secreto")
    with TestClient(crear_app()) as c:
        yield c


def test_health_es_publico(client) -> None:
    assert client.get("/health").status_code == 200


def test_ruta_protegida_sin_token_devuelve_401(client) -> None:
    assert client.get("/medications").status_code == 401


def test_login_invalido_devuelve_401(client) -> None:
    r = client.post("/auth/login", json={"username": "admin", "password": "malo"})
    assert r.status_code == 401


def test_login_y_acceso_con_token(client) -> None:
    r = client.post("/auth/login", json={"username": "admin", "password": "secreto"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert r.json()["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/medications", headers=headers).status_code == 200
    assert client.get("/auth/me", headers=headers).json() == {"username": "admin"}


def test_token_invalido_rechazado(client) -> None:
    headers = {"Authorization": "Bearer token-falso"}
    assert client.get("/medications", headers=headers).status_code == 401
