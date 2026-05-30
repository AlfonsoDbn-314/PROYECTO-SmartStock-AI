"""Asistente basado en Ollama (LLM local), detrás del puerto del dominio.

Genera respuestas en lenguaje natural a partir del contexto recuperado
(inventario en vivo + vault). Si Ollama no está disponible, delega en el
asistente local determinista (degradación elegante). Usa solo la stdlib.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.domain.asistente import Asistente, RespuestaAsistente

from .local import AsistenteLocal

_SISTEMA = (
    "Eres el asistente de un inventario de farmacia (SmartStock). "
    "Respondes en español, de forma breve y precisa. Usa EXCLUSIVAMENTE la "
    "información del contexto proporcionado (inventario actual y documentación). "
    "Si la respuesta no está en el contexto, dilo claramente. No inventes datos "
    "ni medicamentos que no aparezcan en el inventario."
)


class AsistenteOllama(Asistente):
    def __init__(
        self,
        local: AsistenteLocal,
        url: str,
        modelo: str,
        timeout: float = 60.0,
    ) -> None:
        self._local = local
        self._url = url.rstrip("/")
        self._modelo = modelo
        self._timeout = timeout

    def disponible(self) -> bool:
        """Comprueba si el servidor Ollama responde (timeout corto)."""
        try:
            with urllib.request.urlopen(f"{self._url}/api/tags", timeout=2.0):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def ingerir(self) -> int:
        return self._local.ingerir()

    def consultar(self, pregunta: str) -> RespuestaAsistente:
        contexto, fuentes = self._local.construir_contexto(pregunta)
        prompt = (
            f"{_SISTEMA}\n\n"
            f"=== CONTEXTO ===\n{contexto or '(sin datos)'}\n\n"
            f"=== PREGUNTA ===\n{pregunta}\n\n=== RESPUESTA ==="
        )
        try:
            texto = self._generar(prompt)
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            # Degradación elegante: respuesta determinista local.
            return self._local.consultar(pregunta)

        return RespuestaAsistente(
            respuesta=texto.strip(),
            fuentes=fuentes,
            modo=f"ollama:{self._modelo}",
        )

    def _generar(self, prompt: str) -> str:
        cuerpo = json.dumps(
            {"model": self._modelo, "prompt": prompt, "stream": False}
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self._url}/api/generate",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
        respuesta = datos.get("response", "").strip()
        if not respuesta:
            raise ValueError("Ollama devolvió una respuesta vacía.")
        return respuesta
