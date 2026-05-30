"""Asistente RAG en modo local de respaldo (sin OPENAI_API_KEY).

Combina dos fuentes de contexto:
1. Las notas .md del vault de Obsidian (conocimiento estático).
2. El inventario en vivo (medicamentos, stock y caducidad) vía un proveedor.

Para preguntas sobre caducidad/vencimiento o reabastecimiento responde de forma
determinista calculando sobre el inventario; para el resto recupera los
fragmentos más relevantes del vault por solapamiento de términos. Sin ChromaDB
ni OpenAI: funciona siempre.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from app.domain.asistente import Asistente, RespuestaAsistente
from app.domain.caducidad import (
    dias_para_caducar,
    esta_caducado,
    medicamentos_proximos_a_caducar,
)
from app.domain.entities import Medicamento
from app.domain.stock import medicamentos_en_riesgo

_PALABRA = re.compile(r"[\wáéíóúñü]+", re.IGNORECASE)
_VACIAS = {
    "de", "la", "el", "los", "las", "un", "una", "y", "o", "que", "en", "a",
    "del", "se", "por", "con", "para", "su", "al", "lo", "como", "es", "son",
    "qué", "cuál", "cuáles", "debo", "debería", "hay", "mi", "me", "está",
    "están", "cuándo", "dónde", "primero", "siguiente",
}
# Sinónimos → término canónico usado en el vault y en la detección de intención.
_SINONIMOS = {
    "vencer": "caducar", "vence": "caducar", "vencerse": "caducar",
    "vencimiento": "caducidad", "vencido": "caducado", "vencidos": "caducado",
    "expira": "caducar", "expiracion": "caducidad",
    "lote": "medicamento", "lotes": "medicamento",
    "reponer": "reabastecer", "abastecer": "reabastecer",
    "agotado": "stock", "agotarse": "stock",
}

_TERMINOS_CADUCIDAD = {"caducar", "caducidad", "caducado", "proximo", "próximo"}
_TERMINOS_STOCK = {"reabastecer", "reabastecimiento", "stock", "bajo", "minimo", "mínimo"}
_TERMINOS_DISPONIBILIDAD = {
    "tenemos", "hay", "tiene", "tengo", "disponible", "disponibles",
    "existe", "queda", "quedan", "contamos", "dispone",
}


def _normalizar(token: str) -> str:
    return _SINONIMOS.get(token, token)


def _tokenizar(texto: str) -> list[str]:
    return [
        _normalizar(t.lower())
        for t in _PALABRA.findall(texto)
        if t.lower() not in _VACIAS
    ]


@dataclass
class _Fragmento:
    fuente: str
    texto: str
    tokens: set[str]


class AsistenteLocal(Asistente):
    def __init__(
        self,
        ruta_vault: Path | str,
        proveedor_inventario: Callable[[], list[Medicamento]] | None = None,
    ) -> None:
        self._ruta = Path(ruta_vault)
        self._inventario = proveedor_inventario or (lambda: [])
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
                    _Fragmento(
                        fuente=archivo.name,
                        texto=bloque,
                        tokens=set(_tokenizar(bloque)),
                    )
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

    # --- Respuestas basadas en el inventario en vivo ----------------------

    def _responder_caducidad(self, hoy: date) -> RespuestaAsistente | None:
        meds = self._inventario()
        if not meds:
            return None
        ordenados = sorted(meds, key=lambda m: m.fecha_caducidad)
        proximo = ordenados[0]
        dias = dias_para_caducar(proximo, hoy)
        if esta_caducado(proximo, hoy):
            cabecera = (
                f"El medicamento más urgente es {proximo.nombre} ({proximo.sku}): "
                f"ya está CADUCADO desde el {proximo.fecha_caducidad} "
                f"(hace {-dias} días). Debe retirarse del stock."
            )
        else:
            cabecera = (
                f"El próximo medicamento en caducar es {proximo.nombre} "
                f"({proximo.sku}), el {proximo.fecha_caducidad} "
                f"(en {dias} días)."
            )
        proximos = medicamentos_proximos_a_caducar(meds, hoy)
        if proximos:
            detalle = "\n".join(
                f"- {m.nombre} ({m.sku}): caduca el {m.fecha_caducidad} "
                f"(en {dias_para_caducar(m, hoy)} días)"
                for m in proximos
            )
            cuerpo = f"{cabecera}\n\nPróximos a caducar (≤30 días):\n{detalle}"
        else:
            cuerpo = f"{cabecera}\n\nNingún otro medicamento caduca en los próximos 30 días."
        return RespuestaAsistente(respuesta=cuerpo, fuentes=["inventario"], modo="local")

    def _buscar_por_nombre(self, tokens: set[str]) -> list[Medicamento]:
        """Medicamentos cuyo nombre o SKU intersecan con los términos de la consulta."""
        candidatos = tokens - _TERMINOS_DISPONIBILIDAD
        if not candidatos:
            return []
        encontrados = []
        for m in self._inventario():
            etiqueta = set(_tokenizar(f"{m.nombre} {m.sku}"))
            if candidatos & etiqueta:
                encontrados.append(m)
        return encontrados

    def _responder_disponibilidad(
        self, tokens: set[str], hoy: date
    ) -> RespuestaAsistente | None:
        encontrados = self._buscar_por_nombre(tokens)
        if encontrados:
            detalle = "\n".join(
                f"- {m.nombre} ({m.sku}): {m.stock_actual} uds, "
                f"caduca el {m.fecha_caducidad} (en {dias_para_caducar(m, hoy)} días)"
                for m in encontrados
            )
            cuerpo = f"Sí, está en el inventario:\n{detalle}"
            return RespuestaAsistente(cuerpo, fuentes=["inventario"], modo="local")
        # Hubo intención de disponibilidad pero no se encontró el medicamento.
        termino = " ".join(sorted(tokens - _TERMINOS_DISPONIBILIDAD)) or "ese medicamento"
        cuerpo = (
            f"No, no tenemos «{termino}» en el inventario actualmente."
        )
        return RespuestaAsistente(cuerpo, fuentes=["inventario"], modo="local")

    def _responder_stock(self, hoy: date) -> RespuestaAsistente | None:
        meds = self._inventario()
        if not meds:
            return None
        en_riesgo = medicamentos_en_riesgo(meds)
        if not en_riesgo:
            cuerpo = "Ningún medicamento está por debajo de su stock mínimo. 🎉"
        else:
            detalle = "\n".join(
                f"- {m.nombre} ({m.sku}): {m.stock_actual} uds (mínimo {m.stock_minimo})"
                for m in en_riesgo
            )
            cuerpo = f"Medicamentos que necesitan reabastecimiento:\n{detalle}"
        return RespuestaAsistente(respuesta=cuerpo, fuentes=["inventario"], modo="local")

    # --- Punto de entrada --------------------------------------------------

    def consultar(self, pregunta: str) -> RespuestaAsistente:
        hoy = date.today()
        tokens = set(_tokenizar(pregunta))

        if tokens & _TERMINOS_CADUCIDAD:
            r = self._responder_caducidad(hoy)
            if r is not None:
                return r
        if tokens & _TERMINOS_STOCK:
            r = self._responder_stock(hoy)
            if r is not None:
                return r
        if tokens & _TERMINOS_DISPONIBILIDAD or self._buscar_por_nombre(tokens):
            r = self._responder_disponibilidad(tokens, hoy)
            if r is not None:
                return r

        # Pregunta general: recuperar contexto del vault.
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
        respuesta = (
            "Según la documentación del vault:\n\n"
            f"{contexto}\n\n"
            "(Respuesta generada en modo local de respaldo, sin modelo externo.)"
        )
        return RespuestaAsistente(respuesta=respuesta, fuentes=fuentes, modo="local")

    # --- Contexto para un LLM externo (Ollama) ----------------------------

    def construir_contexto(self, pregunta: str) -> tuple[str, list[str]]:
        """Compone el contexto (inventario en vivo + vault) para un LLM externo."""
        hoy = date.today()
        partes: list[str] = []
        fuentes: list[str] = []

        meds = self._inventario()
        if meds:
            lineas = "\n".join(
                f"- {m.nombre} (SKU {m.sku}, categoría {m.categoria}): "
                f"{m.stock_actual} uds (mínimo {m.stock_minimo}); "
                f"caduca el {m.fecha_caducidad} (en {dias_para_caducar(m, hoy)} días)"
                for m in sorted(meds, key=lambda x: x.fecha_caducidad)
            )
            partes.append(f"INVENTARIO ACTUAL ({hoy}):\n{lineas}")
            fuentes.append("inventario")

        relevantes = self._recuperar(pregunta)
        if relevantes:
            doc = "\n\n".join(f.texto for f in relevantes)
            partes.append(f"DOCUMENTACIÓN:\n{doc}")
            fuentes.extend(f.fuente for f in relevantes)

        return "\n\n".join(partes), list(dict.fromkeys(fuentes))
