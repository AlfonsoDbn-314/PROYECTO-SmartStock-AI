"""Agregaciones puras de dominio para reportes de inventario.

Inventario de medicamentos por lotes y bodegas: no se manejan precios. El
reporte se centra en unidades, distribución por categoría y bodega, riesgo de
quiebre de stock y estado de caducidad de los lotes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .caducidad import DIAS_AVISO_CADUCIDAD, lotes_caducados, lotes_proximos_a_caducar
from .entities import Lote, Medicamento
from .stock import stock_total


@dataclass
class MedicamentoEnRiesgo:
    """Medicamento por debajo de su stock mínimo (con su stock total)."""

    medicamento: Medicamento
    stock_total: int


@dataclass
class ReporteInventario:
    total_medicamentos: int
    total_lotes: int
    total_unidades: int
    unidades_por_categoria: dict[str, int]
    unidades_por_bodega: dict[str, int]
    medicamentos_en_riesgo: list[MedicamentoEnRiesgo] = field(default_factory=list)
    lotes_proximos_a_caducar: list[Lote] = field(default_factory=list)
    lotes_caducados: list[Lote] = field(default_factory=list)


def generar_reporte(
    medicamentos: list[Medicamento],
    lotes: list[Lote],
    hoy: date,
    dias_aviso: int = DIAS_AVISO_CADUCIDAD,
) -> ReporteInventario:
    """Calcula el reporte agregado a partir de medicamentos y lotes."""
    lotes_por_med: dict[str, list[Lote]] = {}
    unidades_por_categoria: dict[str, int] = {}
    unidades_por_bodega: dict[str, int] = {}

    for lote in lotes:
        lotes_por_med.setdefault(lote.medicamento_id, []).append(lote)
        unidades_por_bodega[lote.bodega_codigo] = (
            unidades_por_bodega.get(lote.bodega_codigo, 0) + lote.stock_actual
        )

    en_riesgo: list[MedicamentoEnRiesgo] = []
    for m in medicamentos:
        sus_lotes = lotes_por_med.get(m.id, [])
        total = stock_total(sus_lotes)
        unidades_por_categoria[m.categoria] = (
            unidades_por_categoria.get(m.categoria, 0) + total
        )
        if total < m.stock_minimo:
            en_riesgo.append(MedicamentoEnRiesgo(medicamento=m, stock_total=total))

    return ReporteInventario(
        total_medicamentos=len(medicamentos),
        total_lotes=len(lotes),
        total_unidades=stock_total(lotes),
        unidades_por_categoria=unidades_por_categoria,
        unidades_por_bodega=unidades_por_bodega,
        medicamentos_en_riesgo=en_riesgo,
        lotes_proximos_a_caducar=lotes_proximos_a_caducar(lotes, hoy, dias_aviso),
        lotes_caducados=lotes_caducados(lotes, hoy),
    )
