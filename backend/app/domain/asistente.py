"""Puerto del asistente conversacional (RAG).

El dominio define el contrato; la recuperación e indexación concretas viven
en ``adapters/rag``. Sin dependencias de ChromaDB ni OpenAI aquí.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RespuestaAsistente:
    respuesta: str
    fuentes: list[str] = field(default_factory=list)
    modo: str = "local"


class Asistente(ABC):
    """Puerto de consulta y de ingesta de conocimiento."""

    @abstractmethod
    def consultar(self, pregunta: str) -> RespuestaAsistente:
        """Responde una pregunta usando el contexto recuperado del vault."""
        raise NotImplementedError

    @abstractmethod
    def ingerir(self) -> int:
        """(Re)indexa el vault y devuelve el número de documentos indexados."""
        raise NotImplementedError
