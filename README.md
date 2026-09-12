# AI Software Engineering Team

Sistema multi-agente donde varios agentes de IA colaboran para resolver una tarea de programación de principio a fin: planificación, investigación, diseño técnico, implementación, testing en sandbox y revisión — con reintentos automáticos y progreso visible en tiempo real.

## Índice

- [Arquitectura](#arquitectura)
- [Stack](#stack)
- [Los seis agentes](#los-seis-agentes)
- [Flujo de ejecución](#flujo-de-ejecución)
- [Puesta en marcha](#puesta-en-marcha)
- [API](#api)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Limitaciones conocidas y deuda técnica](#limitaciones-conocidas-y-deuda-técnica)
- [Roadmap](#roadmap)

## Arquitectura

```
Frontend (React + Vite)
   │  REST (crear/consultar tarea) + SSE (progreso en vivo)
   ▼
FastAPI
   │  POST /tasks → TaskExecutor (BackgroundTasks) → build_graph()
   ▼
LangGraph (grafo de 6 agentes + 2 ciclos de retry)
   │  cada nodo: LLMProvider (Groq/Gemini) + herramientas (RAG, Docker sandbox)
   ▼
PostgreSQL + pgvector
   - tasks              → estado/resultado persistente de cada tarea
   - checkpoints         → estado del grafo, persistente entre reinicios
   - knowledge_chunks    → base de conocimiento para RAG
```

Principios de diseño:

- **Servicios desacoplados por interfaz** (Strategy + Adapter + Factory): `LLMProvider`, `EmbeddingProvider` y `TaskExecutor` son interfaces con implementaciones intercambiables por configuración, sin tocar el código que las usa. El servicio LLM además incluye **fallback automático**: si el proveedor primario falla con un error recuperable (rate limit, sobrecarga, timeout), se reintenta automáticamente con un proveedor secundario, de forma transparente para los agentes.
- **Estado del grafo tipado y validado**: `GraphState` (TypedDict con reducers) contiene modelos Pydantic por cada bloque de datos (`Plan`, `ArchitectureSpec`, `CodeArtifacts`, `TestResult`, `ReviewFeedback`), extensible sin romper agentes existentes.
- **Validación de restricciones de la tarea**: Planner detecta restricciones técnicas explícitas en la petición del usuario (ej. "persistencia en memoria", "no usar SQLAlchemy") y las añade al plan; Architect las incorpora al diseño; Reviewer verifica explícitamente su cumplimiento en el código final y fuerza `changes_requested` si detecta alguna violación — incluso si el propio LLM, por error, hubiera marcado la revisión como aprobada. **Esta validación se realiza mediante juicio del LLM, no mediante análisis estático de código: no ofrece una garantía determinista de cumplimiento**, solo reduce la probabilidad de que una restricción explícita pase desapercibida.
- **Agentes construidos con Template Method** (`BaseAgent`): cada agente concreto solo declara `system_prompt`, cómo lee el estado, su schema de salida y cómo escribe el resultado — el flujo de ejecución, reintentos de parseo, tool-calling y manejo de errores es común y vive una sola vez.
- **Persistencia real**: checkpoints de LangGraph en Postgres (sobreviven a reinicios del proceso), tracking de tareas en tabla `tasks` separada del estado interno del grafo, incluyendo tokens usados y coste estimado por tarea.
- **Streaming de eventos**: cada agente emite eventos (`agent_started`, `agent_completed`, `agent_error`, `tool_used`, `retry`) a un bus en memoria, consumidos vía SSE por el frontend.

## Stack

- **Backend**: Python, FastAPI, LangGraph, SQLAlchemy (async), pgvector
- **LLM**: Groq (`openai/gpt-oss-20b`) y Gemini, intercambiables por configuración
- **Embeddings**: Gemini (`gemini-embedding-001`)
- **Base de datos**: PostgreSQL 16 + pgvector (Docker)
- **Sandbox de tests**: contenedor Docker aislado (sin red, límites de CPU/memoria)
- **Frontend**: React + TypeScript + Vite (SPA, sin SSR)

## Los seis agentes

| Agente | Responsabilidad | Usa LLM | Usa tools |
|---|---|---|---|
| **Planner** | Descompone la tarea en pasos ordenados | Sí | No |
| **Researcher** | Investiga contexto relevante vía RAG (pgvector) | Sí | Sí (retrieval) |
| **Architect** | Define especificación técnica y estructura de archivos | Sí | No |
| **Developer** | Implementa el código según la especificación | Sí | No |
| **Tester** | Ejecuta los tests generados en un sandbox Docker aislado | No | — |
| **Reviewer** | Revisa el código final y aprueba o solicita cambios | Sí | No |

## Flujo de ejecución

```
Planner → Researcher → Architect → Developer ⇄ Tester → Reviewer
                                        ▲                   │
                                        └──── (retry) ───────┘
```

- Si los tests fallan, el ciclo vuelve a Developer con el feedback del fallo (incluyendo pistas específicas para errores de import/sintaxis vs. errores de lógica).
- Si el Reviewer solicita cambios, también vuelve a Developer.
- Ambos ciclos comparten un único contador de reintentos (circuit breaker, `MAX_DEVELOPER_RETRIES = 3`) para evitar loops indefinidos.
- Un fallo del proveedor LLM en Developer no testea código obsoleto: se detecta explícitamente (`developer_last_run_failed`) y el grafo decide retry/give_up sin pasar por Tester.

## Puesta en marcha

### Requisitos

- Python 3.12, Node.js, Docker.
- API keys de Groq y Gemini (Google AI Studio).

### 1. Infraestructura

```bash
cd infra
docker compose up -d
docker exec -it infra-postgres-1 psql -U aiswe -d aiswe -c "CREATE EXTENSION IF NOT EXISTS vector;"

docker build -t ai-swe-team-sandbox:latest infra/sandbox
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows; en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env         # y rellena las API keys y credenciales de DB (tanto el bloque LLM_* primario como LLM_FALLBACK_* de respaldo)

python scratch_create_tables.py   # crea las tablas de dominio (tasks, knowledge_chunks)
python run.py                      # arranca el backend en :8000 (crea también las tablas de checkpoints)
```

> `run.py` (no `uvicorn` directamente) es necesario en Windows: fuerza `SelectorEventLoop`, requerido por el driver `psycopg` del checkpointer de Postgres.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

## API

| Endpoint | Descripción |
|---|---|
| `POST /tasks` | Crea una tarea y lanza el workflow en background. Body: `{ "original_request": string }` |
| `GET /tasks/{task_id}` | Estado y resultado de una tarea (`queued`/`running`/`completed`/`failed`), incluyendo `total_tokens` y `estimated_cost_usd` |
| `GET /tasks/{task_id}/events` | Stream SSE de eventos en vivo mientras la tarea se ejecuta |
| `GET /health` | Healthcheck |

## Estructura del repositorio

```
backend/
├── app/
│   ├── agents/          # BaseAgent + los 6 agentes concretos + tools (retrieval, docker_runner)
│   ├── api/              # rutas FastAPI y schemas de request/response
│   ├── core/              # TaskExecutor, task_runner, events (SSE), config
│   ├── db/                # modelos SQLAlchemy, repositorio, sesión
│   ├── embeddings/        # servicio de embeddings (Strategy/Adapter/Factory)
│   ├── graph/              # GraphState, build_graph()
│   └── llm/                # servicio LLM (Strategy/Adapter/Factory)
├── run.py
└── requirements.txt

frontend/
├── src/
│   ├── api/, types/, hooks/, components/, pages/
└── vite.config.ts

infra/
├── docker-compose.yml   # Postgres + pgvector
└── sandbox/             # imagen Docker para ejecución de tests
```

## Limitaciones conocidas y hallazgos de validación

Para diagnosticar correctamente un fallo de una tarea, es importante distinguir tres categorías de causa distintas — mezclarlas lleva a "arreglar" lo que no corresponde (por ejemplo, ampliar el sandbox para tapar una desviación del agente):

**1. Errores de infraestructura del sandbox** (corregibles, y ya corregidos cuando se detectaron):
- El sandbox inicialmente solo tenía `pytest`/`email-validator` instalados; se amplió con `fastapi`, `httpx`, `pydantic` y `pytest-asyncio` al detectar que tareas de API REST los necesitaban.
- Se corrigió la resolución de módulos con paquetes (`python -m pytest` en vez de `pytest` suelto) y el encoding UTF-8 al capturar output de tests con caracteres no ASCII.

**2. Errores en el código generado por los agentes** (parte esperada del ciclo de retry, no bugs del sistema):
- Uso de sintaxis de librerías desactualizada respecto a la versión instalada en el sandbox (ej. `httpx.AsyncClient(app=...)`, eliminado en httpx recientes) — mitigado con una instrucción explícita en el prompt de Developer sobre la sintaxis vigente.
- Modelos pequeños (Groq `openai/gpt-oss-20b`) pueden no converger en tests con literales de string complejos (comillas anidadas, escapes) — limitación de capacidad del modelo, no del diseño del sistema.

**3. Decisiones de producto sobre alcance del sandbox** (no son bugs, son límites elegidos conscientemente):
- El sandbox soporta SQLite + SQLAlchemy (vía `aiosqlite`) como stack de persistencia real, además de FastAPI/httpx/pytest-asyncio. No soporta motores de base de datos que requieran un servidor aparte (Postgres, MySQL) porque el sandbox corre con `--network none`.
- **Hallazgo de validación (histórico, ya mitigado)**: en una ejecución con la petición "API CRUD de to-do list... con persistencia en memoria (un diccionario)", Developer introdujo SQLAlchemy y una base de datos real en vez de la persistencia en memoria pedida explícitamente. Este caso motivó la implementación del sistema de validación de restricciones (ver arriba): hoy, un caso equivalente sería detectado por Reviewer como `constraints_violated`, aunque —como se explica arriba— sin garantía determinista al depender de juicio del LLM.

Otras limitaciones de diseño, no relacionadas con lo anterior:
- **`EventBus` en memoria de un solo proceso**: los eventos SSE no sobreviven a un reinicio del backend ni escalan a múltiples workers. Como consecuencia, al consultar una tarea ya finalizada (`TaskLookup`), el frontend reconstruye el estado por-agente desde el checkpoint de forma aproximada (todos los agentes se muestran con el mismo estado final), no con el detalle exacto de cada paso.
- **Sin migraciones formales** (Alembic): el esquema se crea con `Base.metadata.create_all()`.

- **`estimated_cost_usd` es orientativo, no facturación real**: usa una tabla de precios aproximada (`app/core/pricing.py`) por nombre de modelo, y no distingue si algunos tokens de la tarea se generaron vía el proveedor de fallback (usa siempre la tarifa del proveedor primario configurado).

## Roadmap

- [ ] **Validación de restricciones por código, no solo por LLM**: para restricciones objetivas y mecánicamente verificables (ej. "no importar `sqlalchemy`"), complementar el juicio de Reviewer con un análisis estático simple (grep de imports prohibidos, por ejemplo) que dé una garantía determinista en esos casos concretos.
- [ ] Evaluación offline / golden set con LLM-as-judge
- [ ] Persistir eventos (no solo el estado final) para reconstruir el detalle exacto por-agente al consultar tareas antiguas