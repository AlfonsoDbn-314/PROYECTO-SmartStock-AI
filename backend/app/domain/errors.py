"""Errores del dominio."""
from __future__ import annotations


class ErrorDeDominio(Exception):
    """Error base de las reglas de negocio."""


class StockInsuficienteError(ErrorDeDominio):
    """Se intentó retirar más stock del disponible."""

    def __init__(self, stock_actual: int, cantidad: int) -> None:
        self.stock_actual = stock_actual
        self.cantidad = cantidad
        super().__init__(
            f"Stock insuficiente: disponible {stock_actual}, "
            f"solicitado {cantidad}."
        )


class MedicamentoNoEncontradoError(ErrorDeDominio):
    """No existe el medicamento referenciado."""

    def __init__(self, medicamento_id: str) -> None:
        self.medicamento_id = medicamento_id
        super().__init__(f"Medicamento no encontrado: {medicamento_id}.")
