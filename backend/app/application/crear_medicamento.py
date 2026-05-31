"""Caso de uso: dar de alta un medicamento en el catálogo."""
from __future__ import annotations

import uuid
from typing import Callable

from app.domain.entities import Medicamento
from app.domain.ports import InventarioRepository

from .comandos import CrearMedicamentoCmd


class SkuDuplicadoError(Exception):
    """Ya existe un medicamento con el mismo SKU."""

    def __init__(self, sku: str) -> None:
        self.sku = sku
        super().__init__(f"Ya existe un medicamento con el SKU {sku}.")


class CrearMedicamento:
    def __init__(
        self,
        repo: InventarioRepository,
        id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._repo = repo
        self._id_factory = id_factory

    def ejecutar(self, cmd: CrearMedicamentoCmd) -> Medicamento:
        if self._repo.obtener_medicamento_por_sku(cmd.sku) is not None:
            raise SkuDuplicadoError(cmd.sku)

        medicamento = Medicamento(
            id=self._id_factory(),
            sku=cmd.sku,
            nombre=cmd.nombre,
            categoria=cmd.categoria,
            stock_minimo=cmd.stock_minimo,
        )
        return self._repo.guardar_medicamento(medicamento)
