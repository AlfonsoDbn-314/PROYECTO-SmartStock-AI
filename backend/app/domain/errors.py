"""Errores del dominio."""
from __future__ import annotations


class ErrorDeDominio(Exception):
    """Error base de las reglas de negocio."""


class StockInsuficienteError(ErrorDeDominio):
    """Se intentó retirar más stock del disponible en el lote."""

    def __init__(self, stock_actual: int, cantidad: int) -> None:
        self.stock_actual = stock_actual
        self.cantidad = cantidad
        super().__init__(
            f"Stock insuficiente en el lote: disponible {stock_actual}, "
            f"solicitado {cantidad}."
        )


class MedicamentoNoEncontradoError(ErrorDeDominio):
    """No existe el medicamento referenciado."""

    def __init__(self, medicamento_id: str) -> None:
        self.medicamento_id = medicamento_id
        super().__init__(f"Medicamento no encontrado: {medicamento_id}.")


class LoteNoEncontradoError(ErrorDeDominio):
    """No existe el lote referenciado."""

    def __init__(self, lote_id: str) -> None:
        self.lote_id = lote_id
        super().__init__(f"Lote no encontrado: {lote_id}.")


class BodegaNoEncontradaError(ErrorDeDominio):
    """No existe la bodega referenciada."""

    def __init__(self, bodega_codigo: str) -> None:
        self.bodega_codigo = bodega_codigo
        super().__init__(f"Bodega no encontrada: {bodega_codigo}.")
