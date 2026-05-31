"""Adaptador de persistencia en memoria (implementa el puerto del dominio).

Persistencia elegida para el MVP. PostgreSQL/SQLAlchemy queda para fase 2.
"""
from __future__ import annotations

from app.domain.entities import Bodega, Lote, Medicamento, Movimiento
from app.domain.ports import InventarioRepository


class RepositorioEnMemoria(InventarioRepository):
    def __init__(self) -> None:
        self._bodegas: dict[str, Bodega] = {}
        self._medicamentos: dict[str, Medicamento] = {}
        self._lotes: dict[str, Lote] = {}
        self._movimientos: list[Movimiento] = []

    # --- Bodegas ---
    def guardar_bodega(self, bodega: Bodega) -> Bodega:
        self._bodegas[bodega.codigo] = bodega
        return bodega

    def obtener_bodega(self, codigo: str) -> Bodega | None:
        return self._bodegas.get(codigo)

    def listar_bodegas(self) -> list[Bodega]:
        return list(self._bodegas.values())

    # --- Medicamentos ---
    def guardar_medicamento(self, medicamento: Medicamento) -> Medicamento:
        self._medicamentos[medicamento.id] = medicamento
        return medicamento

    def obtener_medicamento(self, medicamento_id: str) -> Medicamento | None:
        return self._medicamentos.get(medicamento_id)

    def obtener_medicamento_por_sku(self, sku: str) -> Medicamento | None:
        for m in self._medicamentos.values():
            if m.sku == sku:
                return m
        return None

    def listar_medicamentos(self) -> list[Medicamento]:
        return list(self._medicamentos.values())

    # --- Lotes ---
    def guardar_lote(self, lote: Lote) -> Lote:
        self._lotes[lote.id] = lote
        return lote

    def obtener_lote(self, lote_id: str) -> Lote | None:
        return self._lotes.get(lote_id)

    def listar_lotes(self) -> list[Lote]:
        return list(self._lotes.values())

    def listar_lotes_de(self, medicamento_id: str) -> list[Lote]:
        return [x for x in self._lotes.values() if x.medicamento_id == medicamento_id]

    # --- Movimientos ---
    def registrar_movimiento(self, movimiento: Movimiento) -> Movimiento:
        self._movimientos.append(movimiento)
        return movimiento

    def listar_movimientos(self, lote_id: str | None = None) -> list[Movimiento]:
        if lote_id is None:
            return list(self._movimientos)
        return [m for m in self._movimientos if m.lote_id == lote_id]
