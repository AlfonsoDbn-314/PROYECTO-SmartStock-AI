"""Schemas de Pydantic para la API.

Separados de las entidades del dominio (no se mezclan). Traducen entre el
mundo HTTP y los comandos/entidades del dominio.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.application.consultas import MedicamentoConStock
from app.application.movimientos import ResultadoMovimiento
from app.domain.entities import Bodega, Lote
from app.domain.reportes import ReporteInventario


# --- Bodegas ---------------------------------------------------------------

class BodegaOut(BaseModel):
    codigo: str
    nombre: str
    ubicacion: str

    @classmethod
    def desde_dominio(cls, b: Bodega) -> "BodegaOut":
        return cls(codigo=b.codigo, nombre=b.nombre, ubicacion=b.ubicacion)


# --- Medicamentos ----------------------------------------------------------

class CrearMedicamentoIn(BaseModel):
    sku: str = Field(..., examples=["MED-PAR-500"])
    nombre: str = Field(..., examples=["Paracetamol 500mg"])
    categoria: str = Field(..., examples=["Analgésicos"])
    stock_minimo: int = Field(..., ge=0, examples=[50])


class MedicamentoOut(BaseModel):
    id: str
    sku: str
    nombre: str
    categoria: str
    stock_minimo: int
    stock_total: int
    num_lotes: int
    bajo_stock: bool

    @classmethod
    def desde_vista(cls, v: MedicamentoConStock) -> "MedicamentoOut":
        m = v.medicamento
        return cls(
            id=m.id, sku=m.sku, nombre=m.nombre, categoria=m.categoria,
            stock_minimo=m.stock_minimo, stock_total=v.stock_total,
            num_lotes=v.num_lotes, bajo_stock=v.bajo_stock,
        )


# --- Lotes -----------------------------------------------------------------

class LoteOut(BaseModel):
    id: str
    medicamento_id: str
    numero_lote: str
    bodega_codigo: str
    fecha_caducidad: date
    stock_actual: int

    @classmethod
    def desde_dominio(cls, l: Lote) -> "LoteOut":
        return cls(
            id=l.id, medicamento_id=l.medicamento_id, numero_lote=l.numero_lote,
            bodega_codigo=l.bodega_codigo, fecha_caducidad=l.fecha_caducidad,
            stock_actual=l.stock_actual,
        )


class RegistrarEntradaIn(BaseModel):
    medicamento_id: str
    numero_lote: str = Field(..., examples=["L2026-014"])
    bodega_codigo: str = Field(..., examples=["BOD-CENTRAL"])
    fecha_caducidad: date = Field(..., examples=["2027-06-30"])
    cantidad: int = Field(..., gt=0, examples=[50])
    motivo: str | None = None


class RegistrarSalidaIn(BaseModel):
    lote_id: str
    cantidad: int = Field(..., gt=0, examples=[5])
    motivo: str | None = None


class MovimientoResultadoOut(BaseModel):
    movimiento_id: str
    lote: LoteOut
    stock_total_medicamento: int
    bajo_stock: bool

    @classmethod
    def desde_dominio(cls, r: ResultadoMovimiento) -> "MovimientoResultadoOut":
        return cls(
            movimiento_id=r.movimiento.id,
            lote=LoteOut.desde_dominio(r.lote),
            stock_total_medicamento=r.stock_total,
            bajo_stock=r.bajo_stock,
        )


# --- Reporte ---------------------------------------------------------------

class MedicamentoEnRiesgoOut(BaseModel):
    sku: str
    nombre: str
    categoria: str
    stock_total: int
    stock_minimo: int


class ReporteInventarioOut(BaseModel):
    total_medicamentos: int
    total_lotes: int
    total_unidades: int
    unidades_por_categoria: dict[str, int]
    unidades_por_bodega: dict[str, int]
    medicamentos_en_riesgo: list[MedicamentoEnRiesgoOut]
    lotes_proximos_a_caducar: list[LoteOut]
    lotes_caducados: list[LoteOut]

    @classmethod
    def desde_dominio(cls, r: ReporteInventario) -> "ReporteInventarioOut":
        return cls(
            total_medicamentos=r.total_medicamentos,
            total_lotes=r.total_lotes,
            total_unidades=r.total_unidades,
            unidades_por_categoria=r.unidades_por_categoria,
            unidades_por_bodega=r.unidades_por_bodega,
            medicamentos_en_riesgo=[
                MedicamentoEnRiesgoOut(
                    sku=x.medicamento.sku, nombre=x.medicamento.nombre,
                    categoria=x.medicamento.categoria, stock_total=x.stock_total,
                    stock_minimo=x.medicamento.stock_minimo,
                )
                for x in r.medicamentos_en_riesgo
            ],
            lotes_proximos_a_caducar=[LoteOut.desde_dominio(x) for x in r.lotes_proximos_a_caducar],
            lotes_caducados=[LoteOut.desde_dominio(x) for x in r.lotes_caducados],
        )


# --- Asistente -------------------------------------------------------------

class PreguntaIn(BaseModel):
    pregunta: str = Field(..., examples=["¿Qué lote caduca primero y en qué bodega?"])


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
