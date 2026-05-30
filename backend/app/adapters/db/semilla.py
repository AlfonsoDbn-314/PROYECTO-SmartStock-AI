"""Datos semilla para el MVP (paso 4).

Medicamentos de ejemplo con distintos estados de stock y caducidad:
- MED-PAR-500: bajo stock.
- MED-AMOX-250: stock sano.
- MED-IBU-400: bajo stock y próximo a caducar.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.application.comandos import CrearMedicamentoCmd
from app.application.crear_medicamento import CrearMedicamento, SkuDuplicadoError
from app.domain.ports import MedicamentoRepository

_HOY = date.today()

_SEMILLA = [
    # SKU, nombre, categoría, fecha_caducidad, stock_inicial, stock_minimo
    CrearMedicamentoCmd(
        "MED-PAR-500", "Paracetamol 500mg", "Analgésicos",
        _HOY + timedelta(days=180), 8, 10,
    ),
    CrearMedicamentoCmd(
        "MED-AMOX-250", "Amoxicilina 250mg", "Antibióticos",
        _HOY + timedelta(days=400), 40, 15,
    ),
    CrearMedicamentoCmd(
        "MED-IBU-400", "Ibuprofeno 400mg", "Antiinflamatorios",
        _HOY + timedelta(days=15), 5, 12,
    ),
]


def cargar_semilla(repo: MedicamentoRepository) -> None:
    """Inserta los medicamentos de ejemplo si aún no existen (idempotente)."""
    caso = CrearMedicamento(repo)
    for cmd in _SEMILLA:
        try:
            caso.ejecutar(cmd)
        except SkuDuplicadoError:
            continue
