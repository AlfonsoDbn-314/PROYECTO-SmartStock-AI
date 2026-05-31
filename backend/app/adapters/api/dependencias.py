"""Composition root: instancia el repositorio y provee los casos de uso.

Conecta las capas (api → application → domain) inyectando el adaptador de
persistencia concreto detrás del puerto.
"""
from __future__ import annotations

from pathlib import Path

from app.adapters.db.memoria import RepositorioEnMemoria
from app.adapters.rag.local import AsistenteLocal, InventarioSnapshot
from app.adapters.rag.ollama import AsistenteOllama
from app.application.consultas import (
    GenerarReporteInventario,
    ListarAlertasReabastecimiento,
    ListarBodegas,
    ListarLotes,
    ListarLotesProximosACaducar,
    ListarMedicamentos,
)
from app.application.crear_medicamento import CrearMedicamento
from app.application.movimientos import RegistrarEntrada, RegistrarSalida
from app.config.settings import settings
from app.domain.asistente import Asistente
from app.domain.ports import InventarioRepository

_RUTA_VAULT = Path(__file__).resolve().parents[4] / "obsidian-vault"

_repositorio: InventarioRepository = RepositorioEnMemoria()


def obtener_repositorio() -> InventarioRepository:
    return _repositorio


def _snapshot() -> InventarioSnapshot:
    return InventarioSnapshot(
        medicamentos=_repositorio.listar_medicamentos(),
        lotes=_repositorio.listar_lotes(),
        bodegas=_repositorio.listar_bodegas(),
    )


def _crear_asistente() -> Asistente:
    """Usa Ollama si está activo y responde; si no, el modo local determinista."""
    local = AsistenteLocal(_RUTA_VAULT, proveedor_inventario=_snapshot)
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


def obtener_asistente() -> Asistente:
    return _asistente


def get_crear_medicamento() -> CrearMedicamento:
    return CrearMedicamento(_repositorio)


def get_registrar_entrada() -> RegistrarEntrada:
    return RegistrarEntrada(_repositorio)


def get_registrar_salida() -> RegistrarSalida:
    return RegistrarSalida(_repositorio)


def get_listar_bodegas() -> ListarBodegas:
    return ListarBodegas(_repositorio)


def get_listar_medicamentos() -> ListarMedicamentos:
    return ListarMedicamentos(_repositorio)


def get_listar_lotes() -> ListarLotes:
    return ListarLotes(_repositorio)


def get_listar_alertas() -> ListarAlertasReabastecimiento:
    return ListarAlertasReabastecimiento(_repositorio)


def get_listar_proximos_a_caducar() -> ListarLotesProximosACaducar:
    return ListarLotesProximosACaducar(_repositorio)


def get_generar_reporte() -> GenerarReporteInventario:
    return GenerarReporteInventario(_repositorio)
