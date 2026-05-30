"""Composition root: instancia el repositorio y provee los casos de uso.

Aquí se conectan las capas (api → application → domain) inyectando el
adaptador de persistencia concreto detrás del puerto.
"""
from __future__ import annotations

from pathlib import Path

from app.adapters.db.memoria import RepositorioEnMemoria
from app.adapters.rag.local import AsistenteLocal
from app.adapters.rag.ollama import AsistenteOllama
from app.application.consultas import (
    GenerarReporteInventario,
    ListarAlertasReabastecimiento,
    ListarMedicamentos,
    ListarProximosACaducar,
)
from app.application.crear_medicamento import CrearMedicamento
from app.application.registrar_movimiento import RegistrarMovimiento
from app.config.settings import settings
from app.domain.asistente import Asistente
from app.domain.ports import MedicamentoRepository

# Ruta al vault de Obsidian (raiz_repo/obsidian-vault).
_RUTA_VAULT = Path(__file__).resolve().parents[4] / "obsidian-vault"

# Singletons compartidos durante la vida del proceso.
_repositorio: MedicamentoRepository = RepositorioEnMemoria()


def _crear_asistente() -> Asistente:
    """Usa Ollama si está activo y responde; si no, el modo local determinista."""
    # El asistente recibe el inventario en vivo (caducidad/stock/disponibilidad).
    local = AsistenteLocal(
        _RUTA_VAULT, proveedor_inventario=lambda: _repositorio.listar()
    )
    if settings.ollama_enabled:
        ollama = AsistenteOllama(
            local,
            url=settings.ollama_url,
            modelo=settings.ollama_model,
            timeout=settings.ollama_timeout,
        )
        if ollama.disponible():
            return ollama
    return local


_asistente: Asistente = _crear_asistente()


def obtener_repositorio() -> MedicamentoRepository:
    return _repositorio


def obtener_asistente() -> Asistente:
    return _asistente


def get_crear_medicamento() -> CrearMedicamento:
    return CrearMedicamento(_repositorio)


def get_registrar_movimiento() -> RegistrarMovimiento:
    return RegistrarMovimiento(_repositorio)


def get_listar_medicamentos() -> ListarMedicamentos:
    return ListarMedicamentos(_repositorio)


def get_listar_alertas() -> ListarAlertasReabastecimiento:
    return ListarAlertasReabastecimiento(_repositorio)


def get_listar_proximos_a_caducar() -> ListarProximosACaducar:
    return ListarProximosACaducar(_repositorio)


def get_generar_reporte() -> GenerarReporteInventario:
    return GenerarReporteInventario(_repositorio)
