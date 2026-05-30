"""Adaptador de persistencia en memoria (implementa el puerto del dominio).

Persistencia elegida para el MVP. PostgreSQL/SQLAlchemy queda para fase 2.
"""
from __future__ import annotations

from app.domain.entities import Medicamento, Movimiento
from app.domain.ports import MedicamentoRepository


class RepositorioEnMemoria(MedicamentoRepository):
    def __init__(self) -> None:
        self._medicamentos: dict[str, Medicamento] = {}
        self._movimientos: list[Movimiento] = []

    def guardar(self, medicamento: Medicamento) -> Medicamento:
        self._medicamentos[medicamento.id] = medicamento
        return medicamento

    def obtener_por_id(self, medicamento_id: str) -> Medicamento | None:
        return self._medicamentos.get(medicamento_id)

    def obtener_por_sku(self, sku: str) -> Medicamento | None:
        for medicamento in self._medicamentos.values():
            if medicamento.sku == sku:
                return medicamento
        return None

    def listar(self) -> list[Medicamento]:
        return list(self._medicamentos.values())

    def registrar_movimiento(self, movimiento: Movimiento) -> Movimiento:
        self._movimientos.append(movimiento)
        return movimiento

    def listar_movimientos(
        self, medicamento_id: str | None = None
    ) -> list[Movimiento]:
        if medicamento_id is None:
            return list(self._movimientos)
        return [m for m in self._movimientos if m.medicamento_id == medicamento_id]
