"""Routers de FastAPI. Solo orquestan casos de uso; sin lógica de negocio."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.application.comandos import CrearMedicamentoCmd, RegistrarMovimientoCmd
from app.application.consultas import (
    GenerarReporteInventario,
    ListarAlertasReabastecimiento,
    ListarMedicamentos,
    ListarProximosACaducar,
)
from app.application.crear_medicamento import CrearMedicamento
from app.application.registrar_movimiento import RegistrarMovimiento
from app.domain.asistente import Asistente

from . import dependencias as deps
from .schemas import (
    CrearMedicamentoIn,
    IngestaOut,
    MedicamentoOut,
    MovimientoResultadoOut,
    PreguntaIn,
    RegistrarMovimientoIn,
    ReporteInventarioOut,
    RespuestaAsistenteOut,
    SaludOut,
)

router = APIRouter()


@router.get("/health", response_model=SaludOut, tags=["salud"])
def health() -> SaludOut:
    return SaludOut(status="ok")


# --- Medicamentos ----------------------------------------------------------

@router.post(
    "/medications",
    response_model=MedicamentoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["medicamentos"],
)
def crear_medicamento(
    body: CrearMedicamentoIn,
    caso: CrearMedicamento = Depends(deps.get_crear_medicamento),
) -> MedicamentoOut:
    medicamento = caso.ejecutar(
        CrearMedicamentoCmd(
            sku=body.sku,
            nombre=body.nombre,
            categoria=body.categoria,
            fecha_caducidad=body.fecha_caducidad,
            stock_inicial=body.stock_inicial,
            stock_minimo=body.stock_minimo,
        )
    )
    return MedicamentoOut.desde_dominio(medicamento)


@router.get("/medications", response_model=list[MedicamentoOut], tags=["medicamentos"])
def listar_medicamentos(
    caso: ListarMedicamentos = Depends(deps.get_listar_medicamentos),
) -> list[MedicamentoOut]:
    return [MedicamentoOut.desde_dominio(m) for m in caso.ejecutar()]


# --- Inventario ------------------------------------------------------------

@router.post(
    "/inventory/movements",
    response_model=MovimientoResultadoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["inventario"],
)
def registrar_movimiento(
    body: RegistrarMovimientoIn,
    caso: RegistrarMovimiento = Depends(deps.get_registrar_movimiento),
) -> MovimientoResultadoOut:
    resultado = caso.ejecutar(
        RegistrarMovimientoCmd(
            medicamento_id=body.medicamento_id,
            tipo=body.tipo,
            cantidad=body.cantidad,
            motivo=body.motivo,
        )
    )
    return MovimientoResultadoOut(
        movimiento_id=resultado.movimiento.id,
        medicamento=MedicamentoOut.desde_dominio(resultado.medicamento),
        bajo_stock=resultado.bajo_stock,
    )


# --- Alertas ---------------------------------------------------------------

@router.get("/alerts/restock", response_model=list[MedicamentoOut], tags=["alertas"])
def alertas_reabastecimiento(
    caso: ListarAlertasReabastecimiento = Depends(deps.get_listar_alertas),
) -> list[MedicamentoOut]:
    return [MedicamentoOut.desde_dominio(m) for m in caso.ejecutar()]


@router.get("/alerts/expiring", response_model=list[MedicamentoOut], tags=["alertas"])
def alertas_caducidad(
    caso: ListarProximosACaducar = Depends(deps.get_listar_proximos_a_caducar),
) -> list[MedicamentoOut]:
    return [MedicamentoOut.desde_dominio(m) for m in caso.ejecutar()]


# --- Reportes --------------------------------------------------------------

@router.get(
    "/reports/inventory", response_model=ReporteInventarioOut, tags=["reportes"]
)
def reporte_inventario(
    caso: GenerarReporteInventario = Depends(deps.get_generar_reporte),
) -> ReporteInventarioOut:
    return ReporteInventarioOut.desde_dominio(caso.ejecutar())


# --- Asistente (RAG modo local) --------------------------------------------

@router.post(
    "/assistant/query", response_model=RespuestaAsistenteOut, tags=["asistente"]
)
def consultar_asistente(
    body: PreguntaIn,
    asistente: Asistente = Depends(deps.obtener_asistente),
) -> RespuestaAsistenteOut:
    r = asistente.consultar(body.pregunta)
    return RespuestaAsistenteOut(respuesta=r.respuesta, fuentes=r.fuentes, modo=r.modo)


@router.post("/assistant/ingest", response_model=IngestaOut, tags=["asistente"])
def ingerir_vault(
    asistente: Asistente = Depends(deps.obtener_asistente),
) -> IngestaOut:
    return IngestaOut(documentos_indexados=asistente.ingerir())
