"""Caso de uso: registrar un movimiento de inventario y recalcular stock."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from app.domain.entities import Medicamento, Movimiento
from app.domain.errors import MedicamentoNoEncontradoError
from app.domain.ports import MedicamentoRepository
from app.domain.stock import aplicar_movimiento, esta_en_bajo_stock

from .comandos import RegistrarMovimientoCmd


@dataclass
class ResultadoMovimiento:
    """Salida del caso de uso: el movimiento, el medicamento actualizado y la alerta."""

    movimiento: Movimiento
    medicamento: Medicamento
    bajo_stock: bool


class RegistrarMovimiento:
    def __init__(
        self,
        repo: MedicamentoRepository,
        id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._repo = repo
        self._id_factory = id_factory

    def ejecutar(self, cmd: RegistrarMovimientoCmd) -> ResultadoMovimiento:
        medicamento = self._repo.obtener_por_id(cmd.medicamento_id)
        if medicamento is None:
            raise MedicamentoNoEncontradoError(cmd.medicamento_id)

        movimiento = Movimiento(
            id=self._id_factory(),
            medicamento_id=cmd.medicamento_id,
            tipo=cmd.tipo,
            cantidad=cmd.cantidad,
            motivo=cmd.motivo,
        )

        # Regla de dominio: recalcula el stock (puede lanzar StockInsuficienteError).
        aplicar_movimiento(medicamento, movimiento)

        # Persistencia: guarda movimiento y medicamento con el stock ya recalculado.
        self._repo.registrar_movimiento(movimiento)
        self._repo.guardar(medicamento)

        return ResultadoMovimiento(
            movimiento=movimiento,
            medicamento=medicamento,
            bajo_stock=esta_en_bajo_stock(medicamento),
        )
