"""Puertos (interfaces) del dominio.

Definen los contratos que la infraestructura debe implementar en
``adapters/``. El dominio depende de estas abstracciones, nunca al revés.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import Bodega, Lote, Medicamento, Movimiento


class InventarioRepository(ABC):
    """Puerto de persistencia del inventario: medicamentos, bodegas, lotes y movimientos."""

    # --- Bodegas ---
    @abstractmethod
    def guardar_bodega(self, bodega: Bodega) -> Bodega: ...

    @abstractmethod
    def obtener_bodega(self, codigo: str) -> Bodega | None: ...

    @abstractmethod
    def listar_bodegas(self) -> list[Bodega]: ...

    # --- Medicamentos ---
    @abstractmethod
    def guardar_medicamento(self, medicamento: Medicamento) -> Medicamento: ...

    @abstractmethod
    def obtener_medicamento(self, medicamento_id: str) -> Medicamento | None: ...

    @abstractmethod
    def obtener_medicamento_por_sku(self, sku: str) -> Medicamento | None: ...

    @abstractmethod
    def listar_medicamentos(self) -> list[Medicamento]: ...

    # --- Lotes ---
    @abstractmethod
    def guardar_lote(self, lote: Lote) -> Lote: ...

    @abstractmethod
    def obtener_lote(self, lote_id: str) -> Lote | None: ...

    @abstractmethod
    def listar_lotes(self) -> list[Lote]: ...

    @abstractmethod
    def listar_lotes_de(self, medicamento_id: str) -> list[Lote]: ...

    # --- Movimientos ---
    @abstractmethod
    def registrar_movimiento(self, movimiento: Movimiento) -> Movimiento: ...

    @abstractmethod
    def listar_movimientos(self, lote_id: str | None = None) -> list[Movimiento]: ...
