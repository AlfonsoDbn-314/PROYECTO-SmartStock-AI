"""Reglas de negocio puras sobre la caducidad de los lotes."""
from __future__ import annotations

from datetime import date

from .entities import Lote

# Umbral por defecto para considerar un lote "próximo a caducar".
DIAS_AVISO_CADUCIDAD = 30


def dias_para_caducar(lote: Lote, hoy: date) -> int:
    """Días que faltan para la caducidad (negativo si ya caducó)."""
    return (lote.fecha_caducidad - hoy).days


def esta_caducado(lote: Lote, hoy: date) -> bool:
    """El lote ya pasó su fecha de caducidad."""
    return lote.fecha_caducidad < hoy


def proximo_a_caducar(lote: Lote, hoy: date, dias_aviso: int = DIAS_AVISO_CADUCIDAD) -> bool:
    """Aún no caduca pero lo hará dentro del umbral de aviso (en días)."""
    dias = dias_para_caducar(lote, hoy)
    return 0 <= dias <= dias_aviso


def lotes_caducados(lotes: list[Lote], hoy: date) -> list[Lote]:
    """Filtra los lotes ya caducados, ordenados por fecha."""
    caducados = [lote for lote in lotes if esta_caducado(lote, hoy)]
    return sorted(caducados, key=lambda x: x.fecha_caducidad)


def lotes_proximos_a_caducar(
    lotes: list[Lote], hoy: date, dias_aviso: int = DIAS_AVISO_CADUCIDAD
) -> list[Lote]:
    """Filtra los lotes próximos a caducar, ordenados por fecha (FEFO)."""
    proximos = [lote for lote in lotes if proximo_a_caducar(lote, hoy, dias_aviso)]
    return sorted(proximos, key=lambda x: x.fecha_caducidad)
