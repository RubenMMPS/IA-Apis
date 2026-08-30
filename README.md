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

- **Servicios desacoplados por interfaz** (Strategy + Adapter + Factory): `LLMProvider`, `EmbeddingProvider` y `TaskExecutor` son interfaces con implementaciones intercambiables por configuración, sin tocar el código que las usa.
- **Estado del grafo tipado y validado**: `GraphState` (TypedDict con reducers) contiene modelos Pydantic por cada bloque de datos (`Plan`, `ArchitectureSpec`, `CodeArtifacts`, `TestResult`, `ReviewFeedback`), extensible sin romper agentes existentes.
- **Agentes construidos con Template Method** (`BaseAgent`): cada agente concreto solo declara `system_prompt`, cómo lee el estado, su schema de salida y cómo escribe el resultado — el flujo de ejecución, reintentos de parseo, tool-calling y manejo de errores es común y vive una sola vez.
- **Persistencia real**: checkpoints de LangGraph en Postgres (sobreviven a reinicios del proceso), tracking de tareas en tabla `tasks` separada del estado interno del grafo.
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

cp .env.example .env         # y rellena las API keys y credenciales de DB

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
| `GET /tasks/{task_id}` | Estado y resultado de una tarea (`queued`/`running`/`completed`/`failed`) |
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

## Limitaciones conocidas y deuda técnica

- **`GeminiProvider` no soporta tool-calling**: si `LLM_PROVIDER=gemini`, el Researcher no ejecuta RAG real (no falla, pero investiga solo con el conocimiento general del modelo, sin consultar `knowledge_chunks`). RAG real requiere `LLM_PROVIDER=groq`.
- **Retry con circuit breaker solo implementado explícitamente para Developer**: un fallo de LLM en Planner/Researcher/Architect no tiene su propio ciclo de retry dedicado (mitigado con guardas defensivas puntuales, no generalizado).
- **Modelos pequeños (Groq `openai/gpt-oss-20b`) pueden no converger** en tests con literales de string complejos (comillas anidadas, escapes) — limitación de capacidad del modelo, no del diseño.
- **`EventBus` en memoria de un solo proceso**: los eventos SSE no sobreviven a un reinicio del backend ni escalan a múltiples workers (mismo tipo de limitación que ya se resolvió para los checkpoints, pendiente aquí).
- **El frontend no expone el código generado**, solo un resumen textual (`result_summary`); el código completo vive en el checkpoint pero no está expuesto vía API todavía.
- **Sin migraciones formales** (Alembic): el esquema se crea con `Base.metadata.create_all()`.

## Roadmap

- [ ] Suite de tests automatizados (pytest) sobre el propio backend
- [ ] Evaluación offline / golden set con LLM-as-judge
- [ ] Exponer `code_artifacts` vía API + visor de código en el frontend
- [ ] Consulta de tareas existentes por `task_id` en el frontend (`TaskLookup`)
- [ ] Tool-calling en `GeminiProvider` (paridad con Groq)
- [ ] Generalizar retry/circuit breaker a todos los agentes, no solo Developer
- [ ] Métricas de coste/tokens por tarea