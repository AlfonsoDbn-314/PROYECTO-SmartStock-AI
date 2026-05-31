"""Casos de uso de lectura: listados, alertas (stock y caducidad) y reporte."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.caducidad import DIAS_AVISO_CADUCIDAD, lotes_proximos_a_caducar
from app.domain.entities import Bodega, Lote, Medicamento
from app.domain.ports import InventarioRepository
from app.domain.reportes import ReporteInventario, generar_reporte
from app.domain.stock import esta_en_bajo_stock, stock_total


@dataclass
class MedicamentoConStock:
    """Vista de un medicamento con su stock total y número de lotes."""

    medicamento: Medicamento
    stock_total: int
    num_lotes: int
    bajo_stock: bool


class ListarBodegas:
    def __init__(self, repo: InventarioRepository) -> None:
        self._repo = repo

    def ejecutar(self) -> list[Bodega]:
        return self._repo.listar_bodegas()


class ListarMedicamentos:
    def __init__(self, repo: InventarioRepository) -> None:
        self._repo = repo

    def ejecutar(self) -> list[MedicamentoConStock]:
        salida = []
        for m in self._repo.listar_medicamentos():
            lotes = self._repo.listar_lotes_de(m.id)
            salida.append(
                MedicamentoConStock(
                    medicamento=m,
                    stock_total=stock_total(lotes),
                    num_lotes=len(lotes),
                    bajo_stock=esta_en_bajo_stock(m, lotes),
                )
            )
        return salida


class ListarLotes:
    """Lista lotes, opcionalmente filtrados por bodega."""

    def __init__(self, repo: InventarioRepository) -> None:
        self._repo = repo

    def ejecutar(self, bodega_codigo: str | None = None) -> list[Lote]:
        lotes = self._repo.listar_lotes()
        if bodega_codigo:
            lotes = [x for x in lotes if x.bodega_codigo == bodega_codigo]
        return sorted(lotes, key=lambda x: x.fecha_caducidad)


class ListarAlertasReabastecimiento:
    """Medicamentos cuyo stock total está por debajo del mínimo."""

    def __init__(self, repo: InventarioRepository) -> None:
        self._repo = repo

    def ejecutar(self) -> list[MedicamentoConStock]:
        return [m for m in ListarMedicamentos(self._repo).ejecutar() if m.bajo_stock]


class ListarLotesProximosACaducar:
    """Lotes que caducan dentro del umbral de aviso."""

    def __init__(self, repo: InventarioRepository) -> None:
        self._repo = repo

    def ejecutar(
        self, hoy: date | None = None, dias_aviso: int = DIAS_AVISO_CADUCIDAD
    ) -> list[Lote]:
        return lotes_proximos_a_caducar(
            self._repo.listar_lotes(), hoy or date.today(), dias_aviso
        )


class GenerarReporteInventario:
    def __init__(self, repo: InventarioRepository) -> None:
        self._repo = repo

    def ejecutar(self, hoy: date | None = None) -> ReporteInventario:
        return generar_reporte(
            self._repo.listar_medicamentos(),
            self._repo.listar_lotes(),
            hoy or date.today(),
        )
