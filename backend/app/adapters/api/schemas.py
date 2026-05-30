"""Schemas de Pydantic para la API.

Separados de las entidades del dominio (no se mezclan). Traducen entre el
mundo HTTP y los comandos/entidades del dominio.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities import Medicamento, TipoMovimiento
from app.domain.reportes import ReporteInventario


# --- Medicamentos ----------------------------------------------------------

class CrearMedicamentoIn(BaseModel):
    sku: str = Field(..., examples=["MED-PAR-500"])
    nombre: str = Field(..., examples=["Paracetamol 500mg"])
    categoria: str = Field(..., examples=["Analgésicos"])
    fecha_caducidad: date = Field(..., examples=["2027-01-31"])
    stock_inicial: int = Field(..., ge=0, examples=[8])
    stock_minimo: int = Field(..., ge=0, examples=[10])


class MedicamentoOut(BaseModel):
    id: str
    sku: str
    nombre: str
    categoria: str
    fecha_caducidad: date
    stock_actual: int
    stock_minimo: int
    bajo_stock: bool

    @classmethod
    def desde_dominio(cls, m: Medicamento) -> "MedicamentoOut":
        return cls(
            id=m.id,
            sku=m.sku,
            nombre=m.nombre,
            categoria=m.categoria,
            fecha_caducidad=m.fecha_caducidad,
            stock_actual=m.stock_actual,
            stock_minimo=m.stock_minimo,
            bajo_stock=m.stock_actual < m.stock_minimo,
        )


# --- Movimientos -----------------------------------------------------------

class RegistrarMovimientoIn(BaseModel):
    medicamento_id: str
    tipo: TipoMovimiento
    cantidad: int = Field(..., gt=0, examples=[2])
    motivo: str | None = None


class MovimientoResultadoOut(BaseModel):
    movimiento_id: str
    medicamento: MedicamentoOut
    bajo_stock: bool


# --- Reporte ---------------------------------------------------------------

class ReporteInventarioOut(BaseModel):
    total_medicamentos: int
    total_unidades: int
    unidades_por_categoria: dict[str, int]
    medicamentos_en_riesgo: list[MedicamentoOut]
    proximos_a_caducar: list[MedicamentoOut]
    caducados: list[MedicamentoOut]

    @classmethod
    def desde_dominio(cls, r: ReporteInventario) -> "ReporteInventarioOut":
        m = MedicamentoOut.desde_dominio
        return cls(
            total_medicamentos=r.total_medicamentos,
            total_unidades=r.total_unidades,
            unidades_por_categoria=r.unidades_por_categoria,
            medicamentos_en_riesgo=[m(x) for x in r.medicamentos_en_riesgo],
            proximos_a_caducar=[m(x) for x in r.proximos_a_caducar],
            caducados=[m(x) for x in r.caducados],
        )


# --- Asistente -------------------------------------------------------------

class PreguntaIn(BaseModel):
    pregunta: str = Field(..., examples=["¿Qué medicamentos debería reabastecer?"])


class RespuestaAsistenteOut(BaseModel):
    respuesta: str
    fuentes: list[str]
    modo: str


class IngestaOut(BaseModel):
    documentos_indexados: int


# --- Salud -----------------------------------------------------------------

class SaludOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})
    status: str = "ok"
