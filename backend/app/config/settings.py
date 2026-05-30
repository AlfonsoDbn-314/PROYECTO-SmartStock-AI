"""Configuración de la aplicación."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SMARTSTOCK_", extra="ignore")

    app_name: str = "SmartStock AI"
    # Cargar medicamentos de ejemplo al arrancar (paso 4 del MVP).
    cargar_semilla: bool = True

    # --- Asistente / Ollama ---
    # Si está activo y Ollama responde, se usa el LLM real; si no, modo local.
    ollama_enabled: bool = True
    ollama_url: str = "http://localhost:11434"
    # Modelos que caben en ~6 GB de VRAM (Q4): llama3.2:3b, qwen2.5:3b,
    # gemma2:2b, phi3.5:3.8b.
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: float = 60.0


settings = Settings()
