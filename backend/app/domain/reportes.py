"""Agregaciones puras de dominio para reportes de inventario.

Inventario de medicamentos: no se manejan precios. El reporte se centra en
unidades, categorías, riesgo de quiebre de stock y estado de caducidad.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .caducidad import (
    DIAS_AVISO_CADUCIDAD,
    medicamentos_caducados,
    medicamentos_proximos_a_caducar,
)
from .entities import Medicamento
from .stock import medicamentos_en_riesgo


@dataclass
class ReporteInventario:
    """Resultado agregado del estado del inventario de medicamentos.

    Atributos:
        total_medicamentos: Número de medicamentos distintos.
        total_unidades: Suma de unidades en stock.
        unidades_por_categoria: Unidades en stock agrupadas por categoría.
        medicamentos_en_riesgo: Medicamentos por debajo del stock mínimo.
        proximos_a_caducar: Medicamentos que caducan dentro del umbral de aviso.
        caducados: Medicamentos que ya pasaron su fecha de caducidad.
    """

    total_medicamentos: int
    total_unidades: int
    unidades_por_categoria: dict[str, int]
    medicamentos_en_riesgo: list[Medicamento] = field(default_factory=list)
    proximos_a_caducar: list[Medicamento] = field(default_factory=list)
    caducados: list[Medicamento] = field(default_factory=list)


def generar_reporte(
    medicamentos: list[Medicamento],
    hoy: date,
    dias_aviso: int = DIAS_AVISO_CADUCIDAD,
) -> ReporteInventario:
    """Calcula el reporte agregado a partir de una lista de medicamentos."""
    total_unidades = 0
    unidades_por_categoria: dict[str, int] = {}

    for m in medicamentos:
        total_unidades += m.stock_actual
        unidades_por_categoria[m.categoria] = (
            unidades_por_categoria.get(m.categoria, 0) + m.stock_actual
        )

    return ReporteInventario(
        total_medicamentos=len(medicamentos),
        total_unidades=total_unidades,
        unidades_por_categoria=unidades_por_categoria,
        medicamentos_en_riesgo=medicamentos_en_riesgo(medicamentos),
        proximos_a_caducar=medicamentos_proximos_a_caducar(
            medicamentos, hoy, dias_aviso
        ),
        caducados=medicamentos_caducados(medicamentos, hoy),
    )
