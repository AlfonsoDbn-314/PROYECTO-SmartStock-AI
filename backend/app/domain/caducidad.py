"""Reglas de negocio puras sobre la caducidad de los medicamentos."""
from __future__ import annotations

from datetime import date

from .entities import Medicamento

# Umbral por defecto para considerar un medicamento "próximo a caducar".
DIAS_AVISO_CADUCIDAD = 30


def dias_para_caducar(medicamento: Medicamento, hoy: date) -> int:
    """Días que faltan para la caducidad (negativo si ya caducó)."""
    return (medicamento.fecha_caducidad - hoy).days


def esta_caducado(medicamento: Medicamento, hoy: date) -> bool:
    """El medicamento ya pasó su fecha de caducidad."""
    return medicamento.fecha_caducidad < hoy


def proximo_a_caducar(
    medicamento: Medicamento, hoy: date, dias_aviso: int = DIAS_AVISO_CADUCIDAD
) -> bool:
    """Aún no caduca pero lo hará dentro del umbral de aviso (en días)."""
    dias = dias_para_caducar(medicamento, hoy)
    return 0 <= dias <= dias_aviso


def medicamentos_caducados(
    medicamentos: list[Medicamento], hoy: date
) -> list[Medicamento]:
    """Filtra los medicamentos ya caducados."""
    return [m for m in medicamentos if esta_caducado(m, hoy)]


def medicamentos_proximos_a_caducar(
    medicamentos: list[Medicamento],
    hoy: date,
    dias_aviso: int = DIAS_AVISO_CADUCIDAD,
) -> list[Medicamento]:
    """Filtra los medicamentos próximos a caducar, ordenados por fecha."""
    proximos = [m for m in medicamentos if proximo_a_caducar(m, hoy, dias_aviso)]
    return sorted(proximos, key=lambda m: m.fecha_caducidad)
