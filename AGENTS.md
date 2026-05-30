# AGENTS.md — SmartStock AI

## Qué es esto
Sistema de gestión de inventario inteligente con asistente conversacional RAG.
Monolito modular con **arquitectura hexagonal**. Backend FastAPI, frontend React,
pipeline RAG alimentado por un vault de Obsidian.

## OBJETIVO DE HOY: MVP en un día
La prioridad absoluta es una **rebanada vertical funcional**, no completitud.
Meta verificable: crear un producto → registrar una salida → ver que dispara una
alerta de reabastecimiento → verlo en el dashboard → preguntarle algo al asistente.

### Entra hoy
- Productos: alta y listado.
- Movimientos de inventario (entrada/salida) con recálculo de stock.
- Alerta de reabastecimiento (stock actual < stock mínimo).
- Reporte agregado (valor total, categorías, productos en riesgo).
- Asistente RAG en **modo local de respaldo** (sin `OPENAI_API_KEY`): responde
  con el contexto recuperado del vault.

### NO entra hoy (no lo construyas salvo que se pida)
- PostgreSQL → usa el repositorio en memoria.
- Docker para el loop de desarrollo.
- OpenAI real / GPT-4o.
- Suite completa TDD/BDD/E2E (solo tests mínimos, ver abajo).

### Orden de construcción (respétalo)
1. **Dominio**: entidades `Producto`, `Movimiento`, puerto del repositorio y reglas
   de negocio puras (cálculo de stock, decisión de bajo stock). + 2–3 tests de la
   regla de stock.
2. **Casos de uso** en `application/`: crear producto, registrar movimiento,
   listar alertas, generar reporte.
3. **API** en `adapters/api/`: `POST /products`, `GET /products`,
   `POST /inventory/movements`, `GET /alerts/restock`, `GET /reports/inventory`,
   `GET /health`. Validar todo vía Swagger (`/docs`).
4. **Datos semilla** al arrancar: `SKU-CAF-001` (bajo), `SKU-ARR-002` (sano),
   `SKU-LIM-003` (bajo).
5. **Frontend** mínimo: un dashboard React (tabla de productos, formulario de
   movimiento, panel de alertas) consumiendo `/api`. Sacrificable si falta tiempo.
6. **RAG** en modo local: indexar el vault, `POST /assistant/query`,
   `POST /assistant/ingest`.

Si el tiempo aprieta, orden de sacrificio: Docker → frontend → RAG real → tests
extra. Innegociables: pasos 1–3.

## Reglas de arquitectura (CRÍTICO)
- El **dominio NO importa** FastAPI, SQLAlchemy, ChromaDB ni OpenAI. Nada de
  frameworks en `domain/`. Si una regla de negocio necesita infraestructura, va
  detrás de un **puerto** (interfaz) implementado en `adapters/`.
- Las reglas de negocio deben poder probarse sin levantar API ni base de datos.
- Inyecta dependencias hacia adentro: `api → application → domain`.

## Stack
- Python 3.12, FastAPI, Pydantic.
- Persistencia hoy: repositorio en memoria. (PostgreSQL/SQLAlchemy queda para fase 2.)
- RAG: ChromaDB + embeddings, modo local de respaldo sin key.
- Frontend: React 18, TypeScript, Tailwind, Vite. Proxy `/api` → `http://localhost:8000`.

## Estructura del repo
```
backend/app/{domain,application,adapters/{api,db,rag},config}
backend/{features,tests}
frontend/src/{lib,pages}
obsidian-vault/
```

## Convenciones
- Nombres del dominio en español: `Producto`, `Movimiento`, `stock_minimo`,
  `stock_actual`. Snake_case en Python, camelCase en TS.
- Sin lógica de negocio en los controladores de FastAPI; solo orquestan casos de uso.
- Schemas de Pydantic separados de las entidades del dominio (no mezclar).
- Mensajes, comentarios y commits en español.

## Comandos (Windows, desde la raíz del proyecto)
```bat
:: Entorno y dependencias (mínimo, sin el extra rag al inicio)
python -m venv .venv
cd backend
..\.venv\Scripts\python.exe -m pip install -e ".[dev]"

:: Levantar API
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

:: Tests
..\.venv\Scripts\python.exe -m pytest

:: Solo cuando toque el RAG (requiere Build Tools en Windows)
..\.venv\Scripts\python.exe -m pip install -e ".[dev,rag]"
```
Frontend:
```bat
cd frontend && npm install && npm run dev
```

## Definición de "hecho" (MVP)
- `/health` responde `{"status":"ok"}`.
- Flujo completo verificado desde Swagger: producto → movimiento → alerta → reporte.
- Tests de la regla de stock en verde.
- `/assistant/query` devuelve respuesta con contexto del vault en modo local.

## Cómo trabajar conmigo
- Avanza un bloque a la vez; no saltes al siguiente sin validar el actual.
- Antes de escribir código de infraestructura, confirma que el dominio ya está aislado.
- Si algo del alcance "no entra hoy" parece necesario, pregunta antes de construirlo.
