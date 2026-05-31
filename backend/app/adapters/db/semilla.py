"""Datos semilla para el MVP (paso 4).

Carga bodegas, un catálogo amplio de medicamentos y múltiples lotes repartidos
entre bodegas, con distintos estados de stock y caducidad (sanos, bajo stock,
próximos a caducar y caducados) para que el dashboard luzca realista.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.domain.entities import Bodega, Lote, Medicamento
from app.domain.ports import InventarioRepository

_HOY = date.today()


def _d(dias: int) -> date:
    return _HOY + timedelta(days=dias)


# --- Bodegas ---------------------------------------------------------------
_BODEGAS = [
    Bodega("BOD-CENTRAL", "Bodega Central", "Planta baja - Edificio A"),
    Bodega("BOD-FRIO", "Cámara de Frío", "Refrigerados 2-8°C - Edificio A"),
    Bodega("BOD-SUR", "Sucursal Sur", "Av. Sur 1200"),
    Bodega("BOD-NORTE", "Sucursal Norte", "Calle Norte 45"),
]

# --- Medicamentos (sku, nombre, categoría, stock_minimo) -------------------
_MEDICAMENTOS = [
    ("MED-PAR-500", "Paracetamol 500mg", "Analgésicos", 50),
    ("MED-IBU-400", "Ibuprofeno 400mg", "Antiinflamatorios", 40),
    ("MED-AMOX-250", "Amoxicilina 250mg", "Antibióticos", 30),
    ("MED-AZIT-500", "Azitromicina 500mg", "Antibióticos", 20),
    ("MED-OME-20", "Omeprazol 20mg", "Gastrointestinales", 35),
    ("MED-LORA-10", "Loratadina 10mg", "Antihistamínicos", 25),
    ("MED-METF-850", "Metformina 850mg", "Antidiabéticos", 40),
    ("MED-LOSA-50", "Losartán 50mg", "Antihipertensivos", 30),
    ("MED-SALB-INH", "Salbutamol inhalador", "Respiratorios", 15),
    ("MED-INS-NPH", "Insulina NPH", "Antidiabéticos", 20),
    ("MED-DICLO-GEL", "Diclofenaco gel", "Antiinflamatorios", 18),
    ("MED-VITC-1G", "Vitamina C 1g", "Vitaminas", 60),
]

# --- Lotes (sku, numero_lote, bodega, dias_caducidad, stock) ---------------
# dias_caducidad negativo = ya caducado; pequeño = próximo a caducar.
_LOTES = [
    ("MED-PAR-500", "L2025-101", "BOD-CENTRAL", 240, 60),
    ("MED-PAR-500", "L2025-102", "BOD-SUR", 25, 20),
    ("MED-PAR-500", "L2024-090", "BOD-NORTE", -10, 8),
    ("MED-IBU-400", "L2025-210", "BOD-CENTRAL", 400, 30),
    ("MED-IBU-400", "L2025-211", "BOD-SUR", 12, 5),
    ("MED-AMOX-250", "L2025-330", "BOD-CENTRAL", 300, 18),
    ("MED-AMOX-250", "L2025-331", "BOD-NORTE", 20, 6),
    ("MED-AZIT-500", "L2025-410", "BOD-CENTRAL", 150, 25),
    ("MED-OME-20", "L2025-500", "BOD-CENTRAL", 500, 40),
    ("MED-OME-20", "L2025-501", "BOD-SUR", 60, 10),
    ("MED-LORA-10", "L2025-610", "BOD-NORTE", 200, 12),
    ("MED-LORA-10", "L2024-600", "BOD-CENTRAL", -5, 4),
    ("MED-METF-850", "L2025-700", "BOD-CENTRAL", 365, 55),
    ("MED-LOSA-50", "L2025-800", "BOD-SUR", 280, 28),
    ("MED-LOSA-50", "L2025-801", "BOD-NORTE", 18, 7),
    ("MED-SALB-INH", "L2025-900", "BOD-CENTRAL", 120, 9),
    ("MED-INS-NPH", "L2025-950", "BOD-FRIO", 90, 22),
    ("MED-INS-NPH", "L2025-951", "BOD-FRIO", 8, 5),
    ("MED-DICLO-GEL", "L2025-960", "BOD-SUR", 220, 20),
    ("MED-VITC-1G", "L2025-970", "BOD-CENTRAL", 450, 70),
    ("MED-VITC-1G", "L2025-971", "BOD-NORTE", 30, 15),
]


def cargar_semilla(repo: InventarioRepository) -> None:
    """Inserta bodegas, medicamentos y lotes si el repositorio está vacío."""
    if repo.listar_medicamentos():
        return  # idempotente: ya hay datos

    for bodega in _BODEGAS:
        repo.guardar_bodega(bodega)

    sku_a_id: dict[str, str] = {}
    for sku, nombre, categoria, stock_minimo in _MEDICAMENTOS:
        med = Medicamento(
            id=str(uuid.uuid4()),
            sku=sku,
            nombre=nombre,
            categoria=categoria,
            stock_minimo=stock_minimo,
        )
        repo.guardar_medicamento(med)
        sku_a_id[sku] = med.id

    for sku, numero_lote, bodega, dias_cad, stock in _LOTES:
        repo.guardar_lote(
            Lote(
                id=str(uuid.uuid4()),
                medicamento_id=sku_a_id[sku],
                numero_lote=numero_lote,
                bodega_codigo=bodega,
                fecha_caducidad=_d(dias_cad),
                stock_actual=stock,
            )
        )
