"""Asistente RAG en modo local de respaldo (sin OPENAI_API_KEY).

Combina dos fuentes de contexto:
1. Las notas .md del vault de Obsidian (conocimiento estático).
2. El inventario en vivo (medicamentos, lotes y bodegas) vía un proveedor.

Para preguntas sobre caducidad, duración, reabastecimiento, disponibilidad o
bodegas responde de forma determinista calculando sobre el inventario; para el
resto recupera fragmentos del vault. Sin ChromaDB ni OpenAI: funciona siempre.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

from app.domain.asistente import Asistente, RespuestaAsistente
from app.domain.caducidad import dias_para_caducar, esta_caducado, lotes_proximos_a_caducar
from app.domain.entities import Bodega, Lote, Medicamento
from app.domain.stock import esta_en_bajo_stock, stock_total


@dataclass
class InventarioSnapshot:
    """Foto del inventario que el asistente usa como contexto."""

    medicamentos: list[Medicamento] = field(default_factory=list)
    lotes: list[Lote] = field(default_factory=list)
    bodegas: list[Bodega] = field(default_factory=list)


_PALABRA = re.compile(r"[\wáéíóúñü]+", re.IGNORECASE)
_VACIAS = {
    "de", "la", "el", "los", "las", "un", "una", "y", "o", "que", "en", "a",
    "del", "se", "por", "con", "para", "su", "al", "lo", "como", "es", "son",
    "qué", "cuál", "cuáles", "debo", "debería", "hay", "mi", "me", "está",
    "están", "cuándo", "dónde", "va", "ser", "del",
}
_SINONIMOS = {
    "vencer": "caducar", "vence": "caducar", "vencerse": "caducar",
    "vencimiento": "caducidad", "vencido": "caducado", "vencidos": "caducado",
    "expira": "caducar", "expiracion": "caducidad", "caduca": "caducar",
    "reponer": "reabastecer", "abastecer": "reabastecer",
    "agotado": "stock", "agotarse": "stock", "agotandose": "stock",
    "riesgo": "stock", "riesgos": "stock", "critico": "stock",
    "críticos": "stock", "criticos": "stock", "crítico": "stock",
    "faltante": "stock", "faltantes": "stock", "escasez": "stock",
    "almacen": "bodega",
    "durara": "durar", "durará": "durar", "dura": "durar",
}

_TERMINOS_DURACION = {"durar", "ultimo", "último", "lejano", "tarde"}
_TERMINOS_CADUCIDAD = {"caducar", "caducidad", "caducado", "proximo", "próximo"}
_TERMINOS_STOCK = {"reabastecer", "reabastecimiento", "stock", "bajo", "minimo", "mínimo"}
_TERMINOS_DISPONIBILIDAD = {
    "tenemos", "tiene", "tengo", "disponible", "disponibles",
    "existe", "queda", "quedan", "contamos", "dispone",
}
_TERMINOS_BODEGA = {"bodega", "bodegas"}


def _normalizar(token: str) -> str:
    return _SINONIMOS.get(token, token)


def _tokenizar(texto: str) -> list[str]:
    return [_normalizar(t.lower()) for t in _PALABRA.findall(texto) if t.lower() not in _VACIAS]


@dataclass
class _Fragmento:
    fuente: str
    texto: str
    tokens: set[str]


class AsistenteLocal(Asistente):
    def __init__(
        self,
        ruta_vault: Path | str,
        proveedor_inventario: Callable[[], InventarioSnapshot] | None = None,
    ) -> None:
        self._ruta = Path(ruta_vault)
        self._inventario = proveedor_inventario or (lambda: InventarioSnapshot())
        self._fragmentos: list[_Fragmento] = []
        self.ingerir()

    # --- Indexación del vault ---------------------------------------------

    def ingerir(self) -> int:
        self._fragmentos = []
        if not self._ruta.exists():
            return 0
        for archivo in sorted(self._ruta.glob("*.md")):
            contenido = archivo.read_text(encoding="utf-8")
            for bloque in re.split(r"\n\s*\n", contenido):
                bloque = bloque.strip()
                if not bloque:
                    continue
                self._fragmentos.append(
                    _Fragmento(archivo.name, bloque, set(_tokenizar(bloque)))
                )
        return len(self._fragmentos)

    def _recuperar(self, pregunta: str, k: int = 3) -> list[_Fragmento]:
        consulta = set(_tokenizar(pregunta))
        if not consulta:
            return []
        puntuados = [(len(consulta & f.tokens), f) for f in self._fragmentos]
        puntuados = [(s, f) for s, f in puntuados if s > 0]
        puntuados.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in puntuados[:k]]

    # --- Utilidades sobre el inventario -----------------------------------

    def _nombre_med(self, snap: InventarioSnapshot, med_id: str) -> str:
        for m in snap.medicamentos:
            if m.id == med_id:
                return f"{m.nombre} ({m.sku})"
        return med_id

    def _linea_lote(self, snap: InventarioSnapshot, lote: Lote, hoy: date) -> str:
        return (
            f"{self._nombre_med(snap, lote.medicamento_id)} · lote {lote.numero_lote} "
            f"· bodega {lote.bodega_codigo} · {lote.stock_actual} uds · "
            f"caduca {lote.fecha_caducidad} (en {dias_para_caducar(lote, hoy)} días)"
        )

    # --- Respuestas deterministas -----------------------------------------

    def _responder_duracion(self, snap: InventarioSnapshot, hoy: date) -> RespuestaAsistente | None:
        vigentes = [l for l in snap.lotes if not esta_caducado(l, hoy)]
        if not vigentes:
            return None
        lejano = max(vigentes, key=lambda l: l.fecha_caducidad)
        cuerpo = (
            "El lote que durará más tiempo (caduca más tarde) es:\n"
            f"- {self._linea_lote(snap, lejano, hoy)}"
        )
        return RespuestaAsistente(cuerpo, fuentes=["inventario"], modo="local")

    def _responder_caducidad(self, snap: InventarioSnapshot, hoy: date) -> RespuestaAsistente | None:
        if not snap.lotes:
            return None
        vigentes = sorted(
            [l for l in snap.lotes if not esta_caducado(l, hoy)],
            key=lambda l: l.fecha_caducidad,
        )
        caducados = [l for l in snap.lotes if esta_caducado(l, hoy)]
        partes: list[str] = []
        if vigentes:
            partes.append(
                "El próximo lote en caducar es:\n- " + self._linea_lote(snap, vigentes[0], hoy)
            )
        proximos = lotes_proximos_a_caducar(snap.lotes, hoy)
        if proximos:
            detalle = "\n".join("- " + self._linea_lote(snap, l, hoy) for l in proximos)
            partes.append(f"Lotes próximos a caducar (≤30 días):\n{detalle}")
        if caducados:
            detalle = "\n".join("- " + self._linea_lote(snap, l, hoy) for l in caducados)
            partes.append(f"Lotes YA CADUCADOS (retirar):\n{detalle}")
        if not partes:
            return None
        return RespuestaAsistente("\n\n".join(partes), fuentes=["inventario"], modo="local")

    def _lotes_por_med(self, snap: InventarioSnapshot, med_id: str) -> list[Lote]:
        return [l for l in snap.lotes if l.medicamento_id == med_id]

    def _buscar_medicamentos(self, snap: InventarioSnapshot, tokens: set[str]) -> list[Medicamento]:
        candidatos = tokens - _TERMINOS_DISPONIBILIDAD - _TERMINOS_BODEGA
        if not candidatos:
            return []
        encontrados = []
        for m in snap.medicamentos:
            if candidatos & set(_tokenizar(f"{m.nombre} {m.sku}")):
                encontrados.append(m)
        return encontrados

    def _responder_disponibilidad(self, snap, tokens, hoy) -> RespuestaAsistente | None:
        meds = self._buscar_medicamentos(snap, tokens)
        if meds:
            bloques = []
            for m in meds:
                lotes = self._lotes_por_med(snap, m.id)
                total = stock_total(lotes)
                det = "\n".join("    · " + self._linea_lote(snap, l, hoy) for l in lotes) or "    (sin lotes)"
                bloques.append(f"- {m.nombre} ({m.sku}): {total} uds en total\n{det}")
            return RespuestaAsistente("Sí, está en el inventario:\n" + "\n".join(bloques), fuentes=["inventario"], modo="local")
        termino = " ".join(sorted(tokens - _TERMINOS_DISPONIBILIDAD - _TERMINOS_BODEGA)) or "ese medicamento"
        return RespuestaAsistente(f"No, no tenemos «{termino}» en el inventario actualmente.", fuentes=["inventario"], modo="local")

    def _responder_stock(self, snap: InventarioSnapshot, hoy: date) -> RespuestaAsistente | None:
        if not snap.medicamentos:
            return None
        en_riesgo = [m for m in snap.medicamentos if esta_en_bajo_stock(m, self._lotes_por_med(snap, m.id))]
        if not en_riesgo:
            cuerpo = "Ningún medicamento está por debajo de su stock mínimo."
        else:
            detalle = "\n".join(
                f"- {m.nombre} ({m.sku}): {stock_total(self._lotes_por_med(snap, m.id))} uds "
                f"(mínimo {m.stock_minimo})"
                for m in en_riesgo
            )
            cuerpo = f"Medicamentos que necesitan reabastecimiento:\n{detalle}"
        return RespuestaAsistente(cuerpo, fuentes=["inventario"], modo="local")

    def _responder_bodega(self, snap, tokens, hoy) -> RespuestaAsistente | None:
        objetivo = None
        for b in snap.bodegas:
            etiqueta = set(_tokenizar(f"{b.codigo} {b.nombre}"))
            if tokens & etiqueta:
                objetivo = b
                break
        if objetivo is None:
            resumen = "\n".join(f"- {b.codigo}: {b.nombre} ({b.ubicacion})" for b in snap.bodegas)
            return RespuestaAsistente(f"Bodegas registradas:\n{resumen}", fuentes=["inventario"], modo="local")
        lotes = [l for l in snap.lotes if l.bodega_codigo == objetivo.codigo]
        detalle = "\n".join("- " + self._linea_lote(snap, l, hoy) for l in lotes) or "(sin lotes)"
        return RespuestaAsistente(f"Lotes en {objetivo.nombre} ({objetivo.codigo}):\n{detalle}", fuentes=["inventario"], modo="local")

    # --- Punto de entrada --------------------------------------------------

    def consultar(self, pregunta: str) -> RespuestaAsistente:
        hoy = date.today()
        snap = self._inventario()
        tokens = set(_tokenizar(pregunta))

        if tokens & _TERMINOS_DURACION:
            if (r := self._responder_duracion(snap, hoy)) is not None:
                return r
        if tokens & _TERMINOS_CADUCIDAD:
            if (r := self._responder_caducidad(snap, hoy)) is not None:
                return r
        if tokens & _TERMINOS_STOCK:
            if (r := self._responder_stock(snap, hoy)) is not None:
                return r
        if tokens & _TERMINOS_BODEGA:
            if (r := self._responder_bodega(snap, tokens, hoy)) is not None:
                return r
        if tokens & _TERMINOS_DISPONIBILIDAD or self._buscar_medicamentos(snap, tokens):
            if (r := self._responder_disponibilidad(snap, tokens, hoy)) is not None:
                return r

        relevantes = self._recuperar(pregunta)
        if not relevantes:
            return RespuestaAsistente(
                respuesta=(
                    "No encontré información relacionada en el vault ni en el "
                    "inventario. Reformula la pregunta o indexa el contenido con "
                    "/assistant/ingest."
                ),
                fuentes=[],
                modo="local",
            )
        contexto = "\n\n".join(f.texto for f in relevantes)
        fuentes = list(dict.fromkeys(f.fuente for f in relevantes))
        return RespuestaAsistente(
            "Según la documentación del vault:\n\n"
            f"{contexto}\n\n(Respuesta en modo local de respaldo, sin modelo externo.)",
            fuentes=fuentes,
            modo="local",
        )

    # --- Contexto para un LLM externo (Ollama) ----------------------------

    def construir_contexto(self, pregunta: str) -> tuple[str, list[str]]:
        hoy = date.today()
        snap = self._inventario()
        partes: list[str] = []
        fuentes: list[str] = []

        if snap.bodegas:
            partes.append(
                "BODEGAS:\n"
                + "\n".join(f"- {b.codigo}: {b.nombre} ({b.ubicacion})" for b in snap.bodegas)
            )
        if snap.lotes:
            lineas = "\n".join(
                "- " + self._linea_lote(snap, l, hoy)
                for l in sorted(snap.lotes, key=lambda x: x.fecha_caducidad)
            )
            partes.append(f"INVENTARIO POR LOTES ({hoy}):\n{lineas}")
            fuentes.append("inventario")

        relevantes = self._recuperar(pregunta)
        if relevantes:
            doc = "\n\n".join(f.texto for f in relevantes)
            partes.append(f"DOCUMENTACIÓN:\n{doc}")
            fuentes.extend(f.fuente for f in relevantes)

        return "\n\n".join(partes), list(dict.fromkeys(fuentes))
