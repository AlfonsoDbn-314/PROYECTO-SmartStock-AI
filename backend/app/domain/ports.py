"""Puertos (interfaces) del dominio.

Definen los contratos que la infraestructura debe implementar en
``adapters/``. El dominio depende de estas abstracciones, nunca al revés.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import Medicamento, Movimiento


class MedicamentoRepository(ABC):
    """Puerto de persistencia de medicamentos y sus movimientos."""

    @abstractmethod
    def guardar(self, medicamento: Medicamento) -> Medicamento:
        """Crea o actualiza un medicamento y lo devuelve."""
        raise NotImplementedError

    @abstractmethod
    def obtener_por_id(self, medicamento_id: str) -> Medicamento | None:
        """Devuelve el medicamento por su id, o ``None`` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def obtener_por_sku(self, sku: str) -> Medicamento | None:
        """Devuelve el medicamento por su SKU, o ``None`` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def listar(self) -> list[Medicamento]:
        """Devuelve todos los medicamentos."""
        raise NotImplementedError

    @abstractmethod
    def registrar_movimiento(self, movimiento: Movimiento) -> Movimiento:
        """Persiste un movimiento de inventario y lo devuelve."""
        raise NotImplementedError

    @abstractmethod
    def listar_movimientos(
        self, medicamento_id: str | None = None
    ) -> list[Movimiento]:
        """Devuelve los movimientos, opcionalmente filtrados por medicamento."""
        raise NotImplementedError
