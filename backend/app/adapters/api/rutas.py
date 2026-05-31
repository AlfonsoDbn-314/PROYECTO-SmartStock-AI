"""Routers de FastAPI. Solo orquestan casos de uso; sin lógica de negocio."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.application.comandos import (
    CrearMedicamentoCmd,
    RegistrarEntradaCmd,
    RegistrarSalidaCmd,
)
from app.application.consultas import (
    GenerarReporteInventario,
    ListarAlertasReabastecimiento,
    ListarBodegas,
    ListarLotes,
    ListarLotesProximosACaducar,
    ListarMedicamentos,
)
from app.application.crear_medicamento import CrearMedicamento
from app.application.movimientos import RegistrarEntrada, RegistrarSalida
from app.domain.asistente import Asistente

from . import dependencias as deps
from .schemas import (
    BodegaOut,
    CrearMedicamentoIn,
    IngestaOut,
    LoteOut,
    MedicamentoOut,
    MovimientoResultadoOut,
    PreguntaIn,
    RegistrarEntradaIn,
    RegistrarSalidaIn,
    ReporteInventarioOut,
    RespuestaAsistenteOut,
    SaludOut,
)

router = APIRouter()


@router.get("/health", response_model=SaludOut, tags=["salud"])
def health() -> SaludOut:
    return SaludOut(status="ok")


# --- Bodegas ---------------------------------------------------------------

@router.get("/warehouses", response_model=list[BodegaOut], tags=["bodegas"])
def listar_bodegas(caso: ListarBodegas = Depends(deps.get_listar_bodegas)):
    return [BodegaOut.desde_dominio(b) for b in caso.ejecutar()]


# --- Medicamentos ----------------------------------------------------------

@router.post(
    "/medications", response_model=MedicamentoOut,
    status_code=status.HTTP_201_CREATED, tags=["medicamentos"],
)
def crear_medicamento(
    body: CrearMedicamentoIn,
    caso: CrearMedicamento = Depends(deps.get_crear_medicamento),
    listar: ListarMedicamentos = Depends(deps.get_listar_medicamentos),
) -> MedicamentoOut:
    med = caso.ejecutar(
        CrearMedicamentoCmd(
            sku=body.sku, nombre=body.nombre,
            categoria=body.categoria, stock_minimo=body.stock_minimo,
        )
    )
    vista = next(v for v in listar.ejecutar() if v.medicamento.id == med.id)
    return MedicamentoOut.desde_vista(vista)


@router.get("/medications", response_model=list[MedicamentoOut], tags=["medicamentos"])
def listar_medicamentos(caso: ListarMedicamentos = Depends(deps.get_listar_medicamentos)):
    return [MedicamentoOut.desde_vista(v) for v in caso.ejecutar()]


# --- Lotes -----------------------------------------------------------------

@router.get("/lots", response_model=list[LoteOut], tags=["lotes"])
def listar_lotes(
    bodega: str | None = Query(None, description="Filtrar por código de bodega"),
    caso: ListarLotes = Depends(deps.get_listar_lotes),
):
    return [LoteOut.desde_dominio(l) for l in caso.ejecutar(bodega_codigo=bodega)]


# --- Inventario (movimientos) ----------------------------------------------

@router.post(
    "/inventory/entries", response_model=MovimientoResultadoOut,
    status_code=status.HTTP_201_CREATED, tags=["inventario"],
)
def registrar_entrada(
    body: RegistrarEntradaIn,
    caso: RegistrarEntrada = Depends(deps.get_registrar_entrada),
) -> MovimientoResultadoOut:
    r = caso.ejecutar(
        RegistrarEntradaCmd(
            medicamento_id=body.medicamento_id, numero_lote=body.numero_lote,
            bodega_codigo=body.bodega_codigo, fecha_caducidad=body.fecha_caducidad,
            cantidad=body.cantidad, motivo=body.motivo,
        )
    )
    return MovimientoResultadoOut.desde_dominio(r)


@router.post(
    "/inventory/exits", response_model=MovimientoResultadoOut,
    status_code=status.HTTP_201_CREATED, tags=["inventario"],
)
def registrar_salida(
    body: RegistrarSalidaIn,
    caso: RegistrarSalida = Depends(deps.get_registrar_salida),
) -> MovimientoResultadoOut:
    r = caso.ejecutar(
        RegistrarSalidaCmd(lote_id=body.lote_id, cantidad=body.cantidad, motivo=body.motivo)
    )
    return MovimientoResultadoOut.desde_dominio(r)


# --- Alertas ---------------------------------------------------------------

@router.get("/alerts/restock", response_model=list[MedicamentoOut], tags=["alertas"])
def alertas_reabastecimiento(
    caso: ListarAlertasReabastecimiento = Depends(deps.get_listar_alertas),
):
    return [MedicamentoOut.desde_vista(v) for v in caso.ejecutar()]


@router.get("/alerts/expiring", response_model=list[LoteOut], tags=["alertas"])
def alertas_caducidad(
    caso: ListarLotesProximosACaducar = Depends(deps.get_listar_proximos_a_caducar),
):
    return [LoteOut.desde_dominio(l) for l in caso.ejecutar()]


# --- Reportes --------------------------------------------------------------

@router.get("/reports/inventory", response_model=ReporteInventarioOut, tags=["reportes"])
def reporte_inventario(caso: GenerarReporteInventario = Depends(deps.get_generar_reporte)):
    return ReporteInventarioOut.desde_dominio(caso.ejecutar())


# --- Asistente (RAG modo local / Ollama) -----------------------------------

@router.post("/assistant/query", response_model=RespuestaAsistenteOut, tags=["asistente"])
def consultar_asistente(
    body: PreguntaIn, asistente: Asistente = Depends(deps.obtener_asistente)
) -> RespuestaAsistenteOut:
    r = asistente.consultar(body.pregunta)
    return RespuestaAsistenteOut(respuesta=r.respuesta, fuentes=r.fuentes, modo=r.modo)


@router.post("/assistant/ingest", response_model=IngestaOut, tags=["asistente"])
def ingerir_vault(asistente: Asistente = Depends(deps.obtener_asistente)) -> IngestaOut:
    return IngestaOut(documentos_indexados=asistente.ingerir())
