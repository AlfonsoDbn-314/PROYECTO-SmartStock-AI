"""Casos de uso de movimientos de inventario: entradas y salidas por lote."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from app.domain.entities import Lote, Medicamento, Movimiento, TipoMovimiento
from app.domain.errors import (
    BodegaNoEncontradaError,
    LoteNoEncontradoError,
    MedicamentoNoEncontradoError,
)
from app.domain.ports import InventarioRepository
from app.domain.stock import aplicar_movimiento, esta_en_bajo_stock

from .comandos import RegistrarEntradaCmd, RegistrarSalidaCmd


@dataclass
class ResultadoMovimiento:
    movimiento: Movimiento
    lote: Lote
    medicamento: Medicamento
    stock_total: int
    bajo_stock: bool


def _id() -> str:
    return str(uuid.uuid4())


class RegistrarEntrada:
    """Crea o repone un lote (entrada de stock) en una bodega."""

    def __init__(
        self, repo: InventarioRepository, id_factory: Callable[[], str] = _id
    ) -> None:
        self._repo = repo
        self._id_factory = id_factory

    def ejecutar(self, cmd: RegistrarEntradaCmd) -> ResultadoMovimiento:
        medicamento = self._repo.obtener_medicamento(cmd.medicamento_id)
        if medicamento is None:
            raise MedicamentoNoEncontradoError(cmd.medicamento_id)
        if self._repo.obtener_bodega(cmd.bodega_codigo) is None:
            raise BodegaNoEncontradaError(cmd.bodega_codigo)

        # ¿Existe ya el lote (mismo medicamento, número de lote y bodega)?
        lote = next(
            (
                x
                for x in self._repo.listar_lotes_de(cmd.medicamento_id)
                if x.numero_lote == cmd.numero_lote
                and x.bodega_codigo == cmd.bodega_codigo
            ),
            None,
        )
        if lote is None:
            lote = Lote(
                id=self._id_factory(),
                medicamento_id=cmd.medicamento_id,
                numero_lote=cmd.numero_lote,
                bodega_codigo=cmd.bodega_codigo,
                fecha_caducidad=cmd.fecha_caducidad,
                stock_actual=0,
            )

        movimiento = Movimiento(
            id=self._id_factory(),
            lote_id=lote.id,
            tipo=TipoMovimiento.ENTRADA,
            cantidad=cmd.cantidad,
            motivo=cmd.motivo,
        )
        aplicar_movimiento(lote, movimiento)

        self._repo.guardar_lote(lote)
        self._repo.registrar_movimiento(movimiento)
        return self._resultado(movimiento, lote, medicamento)

    def _resultado(self, movimiento, lote, medicamento) -> ResultadoMovimiento:
        lotes = self._repo.listar_lotes_de(medicamento.id)
        from app.domain.stock import stock_total

        return ResultadoMovimiento(
            movimiento=movimiento,
            lote=lote,
            medicamento=medicamento,
            stock_total=stock_total(lotes),
            bajo_stock=esta_en_bajo_stock(medicamento, lotes),
        )


class RegistrarSalida:
    """Descuenta stock de un lote concreto (salida)."""

    def __init__(
        self, repo: InventarioRepository, id_factory: Callable[[], str] = _id
    ) -> None:
        self._repo = repo
        self._id_factory = id_factory

    def ejecutar(self, cmd: RegistrarSalidaCmd) -> ResultadoMovimiento:
        lote = self._repo.obtener_lote(cmd.lote_id)
        if lote is None:
            raise LoteNoEncontradoError(cmd.lote_id)
        medicamento = self._repo.obtener_medicamento(lote.medicamento_id)
        if medicamento is None:
            raise MedicamentoNoEncontradoError(lote.medicamento_id)

        movimiento = Movimiento(
            id=self._id_factory(),
            lote_id=lote.id,
            tipo=TipoMovimiento.SALIDA,
            cantidad=cmd.cantidad,
            motivo=cmd.motivo,
        )
        # Regla de dominio: recalcula el stock del lote (StockInsuficienteError).
        aplicar_movimiento(lote, movimiento)

        self._repo.guardar_lote(lote)
        self._repo.registrar_movimiento(movimiento)

        from app.domain.stock import stock_total

        lotes = self._repo.listar_lotes_de(medicamento.id)
        return ResultadoMovimiento(
            movimiento=movimiento,
            lote=lote,
            medicamento=medicamento,
            stock_total=stock_total(lotes),
            bajo_stock=esta_en_bajo_stock(medicamento, lotes),
        )
