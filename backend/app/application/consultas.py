"""Casos de uso de lectura: listar, alertas (stock y caducidad) y reporte."""
from __future__ import annotations

from datetime import date

from app.domain.caducidad import DIAS_AVISO_CADUCIDAD, medicamentos_proximos_a_caducar
from app.domain.entities import Medicamento
from app.domain.ports import MedicamentoRepository
from app.domain.reportes import ReporteInventario, generar_reporte
from app.domain.stock import medicamentos_en_riesgo


class ListarMedicamentos:
    def __init__(self, repo: MedicamentoRepository) -> None:
        self._repo = repo

    def ejecutar(self) -> list[Medicamento]:
        return self._repo.listar()


class ListarAlertasReabastecimiento:
    """Devuelve los medicamentos cuyo stock está por debajo del mínimo."""

    def __init__(self, repo: MedicamentoRepository) -> None:
        self._repo = repo

    def ejecutar(self) -> list[Medicamento]:
        return medicamentos_en_riesgo(self._repo.listar())


class ListarProximosACaducar:
    """Devuelve los medicamentos que caducan dentro del umbral de aviso."""

    def __init__(self, repo: MedicamentoRepository) -> None:
        self._repo = repo

    def ejecutar(
        self, hoy: date | None = None, dias_aviso: int = DIAS_AVISO_CADUCIDAD
    ) -> list[Medicamento]:
        return medicamentos_proximos_a_caducar(
            self._repo.listar(), hoy or date.today(), dias_aviso
        )


class GenerarReporteInventario:
    def __init__(self, repo: MedicamentoRepository) -> None:
        self._repo = repo

    def ejecutar(self, hoy: date | None = None) -> ReporteInventario:
        return generar_reporte(self._repo.listar(), hoy or date.today())
