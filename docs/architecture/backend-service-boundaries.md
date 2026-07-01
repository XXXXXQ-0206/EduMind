# Backend Service Boundaries

This document records the first step of the EduMind backend migration from a
single FastAPI process toward independently deployable services. The current
runtime remains a modular monolith: public HTTP and WebSocket routes are
unchanged, but route ownership is now explicit in `backend/core/service_registry.py`.

## Current Assembly

`backend/main.py` now delegates application creation to `backend/core/app_factory.py`.
The factory configures middleware, mounts `/storage`, registers public routes,
and wires process lifecycle hooks through FastAPI lifespan handlers.

`backend/service_app.py` can run one boundary at a time when `SERVICE_NAME` is
set. `backend/gateway_app.py` runs a compatibility API gateway that keeps the
old frontend paths stable and proxies them to boundary services.

`backend/core/lifespan.py` owns local process dependencies that must be removed
or externalized during later service extraction:

- SQLite auth database initialization.
- Local Node.js Bilibili MCP bridge startup and shutdown for modular-monolith
  developer mode only. Service-mode deployments use the independent
  `bilibili-bridge` container.

Authentication now supports two validation modes:

- `AUTH_VALIDATION_MODE=local`: validate Bearer tokens against the local SQLite
  auth database. This remains the default for the monolith and identity service.
- `AUTH_VALIDATION_MODE=remote`: validate Bearer tokens through
  `IDENTITY_URL/auth/internal/resolve`. Boundary services use this mode in
  `docker-compose.yml`, which removes their direct dependency on auth table
  reads while preserving the existing `require_auth` dependency.

## Service Boundaries

| Boundary | Current routes | Future ownership |
| --- | --- | --- |
| `identity` | `/auth/*` | Users, sessions, token validation, role-neutral account lifecycle. |
| `learning-content` | `/chat`, `/smartnotes`, `/quiz`, `/flashcards`, `/api/companion/*`, `/exam`, `/debate`, `/tasks`, `/planner` | Student workflows, shared learning workflows, wrongbook, planner, debate, and chat history. |
| `asset-library` | `/files`, `/transcriber` | Upload metadata, object storage, file parsing, transcription entrypoints. |
| `ai-core` | `/ai/internal/invoke` | Internal LLM invocation, provider credentials, and centralized model access. |
| `media-generation` | `/speaking`, `/podcast`, `/api/bilibili/search` | TTS, speech evaluation, podcast audio, Bilibili MCP search, media-facing provider calls. |
| `teaching-content` | `/slides`, `/lesson-plan`, `/paper`, `/teaching-video` | Teacher workflows, slides, lesson plans, papers, teaching video orchestration. |

## Runtime Modes

The backend image uses `scripts/start_backend_service.py` and supports four
roles:

| `BACKEND_ROLE` | Entrypoint | Purpose |
| --- | --- | --- |
| `monolith` or unset | `main:app` | Legacy single-process backend. |
| `gateway` | `gateway_app:app` | Public compatibility gateway on port `5000`. |
| `service` | `service_app:app` | One service boundary selected by `SERVICE_NAME`. |
| `worker` or `task-worker` | `worker_app:main` | Queue consumer for long-running generation tasks. |

The API gateway exposes three health-style endpoints:

- `/health`: lightweight gateway status and configured upstream URLs.
- `/health/live`: process liveness for the gateway itself.
- `/health/ready`: readiness probe that calls each upstream service `/health`
  endpoint and returns `503` when any boundary service is unhealthy or
  unreachable. Docker Compose uses this endpoint for the gateway healthcheck.

`docker-compose.yml` now runs the gateway plus six backend services
(`identity`, `learning-content`, `asset-library`, `ai-core`,
`media-generation`, and `teaching-content`), a `generation-worker`, and the
independent `bilibili-bridge` Node service. Backend services still support the
local `storage/` volume for development, but shared state and generated
artifacts sit behind adapter interfaces. PostgreSQL, Redis, and MinIO services
are included in Compose so deployments can run `KV_STORE_PROVIDER=postgres`,
`EVENT_BUS_PROVIDER=redis`, `TASK_QUEUE_PROVIDER=redis`, and
`OBJECT_STORE_PROVIDER=s3` without changing route code.

## Infrastructure Adapters

Shared state now has explicit adapter boundaries:

| Adapter | Config | Current provider | Next production provider |
| --- | --- | --- | --- |
| Key-value state | `KV_STORE_PROVIDER` | `json` files under `storage/` | `postgres` provider using PostgreSQL JSONB, or dedicated state service |
| Object files | `OBJECT_STORE_PROVIDER` | local filesystem under `storage/` | `s3` provider for S3/MinIO compatible object storage |
| Task events | `EVENT_BUS_PROVIDER` | in-memory process bus | `redis` provider for cross-process Pub/Sub |
| Task leases | `TASK_LEASE_PROVIDER` | KV-backed local lease | `redis` provider for atomic cross-process leases |

`utils.storage.JSONStorage` delegates get/set/delete/update operations through
the KV adapter while keeping the existing API. Listing functions use KV prefix
scans rather than direct `storage/*.json` globbing, so repository-backed
providers can replace JSON files later. High-write list mutations such as file
indexes, planner tasks, flashcards, speaking history, chat messages, quiz
attempts, and debate indexes now use adapter-level atomic updates. The JSON
provider serializes in-process updates per key and writes through atomic file
replacement; the Redis provider uses WATCH/MULTI retries; the PostgreSQL
provider stores records in `edumind_kv(key text primary key, value jsonb not
null, updated_at timestamptz not null default now())` and serializes `update`
operations with a transaction-scoped advisory lock plus row locking.
`KV_STORE_PROVIDER=json` remains the single-process local default to preserve
existing developer data, while Docker Compose defaults services to
`KV_STORE_PROVIDER=postgres`.

`api/routes/files.py`, Planner attachments, Speaking recordings, Podcast audio,
Smart Notes PDFs, lesson-plan PDFs, paper PDFs, slide images/downloads, and
teaching-video local audio/video artifacts now write bytes through the
object-store adapter and keep legacy response fields including `filename`,
`url`, `static`, `file`, `localVideoUrl`, `localAudioUrl`, and download
endpoints. ObjectStore supports `put_bytes`, `put_file`, `get_bytes`, deletion,
prefix deletion, URL generation, and local cache path resolution for legacy
parsers. Feature routes resolve uploaded materials through shared object-key
helpers instead of building `storage/uploads` paths locally. `OBJECT_STORE_PROVIDER=local`
remains the single-process local default, while Docker Compose defaults to the
S3/MinIO provider with MinIO initialized as the shared bucket.

Live WebSocket streams for Chat, Smart Notes, Quiz, Planner, Exam, Paper,
Teaching Video, and Debate now publish through `utils.live_events`, which is
backed by the configured event bus. The old process-local connection manager is
no longer referenced by route modules.

Long-running generators now use `infrastructure.task_lease` for cross-process
de-duplication. Chat, Smart Notes, Quiz, Exam, Paper, Podcast, and Teaching
Video have runner-style execution paths: HTTP create endpoints persist request
state and trigger or enqueue a lease-guarded runner, while WebSocket endpoints
validate access, replay cached state, and subscribe to EventBus. Podcast
generation no longer runs inside `/ws/podcast`; the socket now receives durable
script/audio snapshots plus live events published by the worker. Debate also
uses lease-guarded background tasks for AI replies and analysis. Docker Compose
defaults task leases, live events, and runner dispatch to Redis for the
multi-service topology while preserving inline fallbacks for single-process
development.

Runner dispatch is behind `core.task_dispatcher` and
`infrastructure.task_queue`. `TASK_QUEUE_PROVIDER=inline` starts local runners
inside the API process, which is the local development default.
`TASK_QUEUE_PROVIDER=redis` writes retry-aware `{kind, id, attempts,
max_attempts}` envelopes to `TASK_QUEUE_NAME`. The Redis adapter atomically
moves tasks from the pending list to `TASK_QUEUE_NAME:processing` with
`BRPOPLPUSH`, acknowledges successful work with `LREM`, retries failed work
with incremented attempts, and writes exhausted tasks to
`TASK_QUEUE_NAME:dead`. `backend/worker_app.py` consumes queued work and imports
the route modules that register awaited handlers for `chat`, `smartnotes`,
`quiz`, `exam`, `paper`, `podcast`, and `teaching_video`. Compose includes a
`generation-worker` service for queued work.

LLM calls are centralized through the `ai-core` boundary. Business services and
the worker can run with `LLM_EXECUTION_MODE=remote` and `AI_CORE_URL` pointing to
`http://ai-core:5106`, while the `ai-core` service itself uses
`LLM_EXECUTION_MODE=local` and owns direct provider calls. If
`INTERNAL_SERVICE_TOKEN` is configured, `/ai/internal/invoke` requires
`X-Internal-Service-Token`.

Legacy local data can be migrated through
`scripts/migrate_storage_to_adapters.py`. The command is dry-run by default and
prints a JSON report:

```powershell
python scripts/migrate_storage_to_adapters.py --source-dir storage
```

After configuring `KV_STORE_PROVIDER` and `OBJECT_STORE_PROVIDER` for the
target deployment, pass `--write` to copy restored KV records and artifact files
through the same adapters used by the services:

```powershell
python scripts/migrate_storage_to_adapters.py --source-dir storage --write
```

## Migration Rules

1. Keep the public frontend contract stable until the gateway can proxy old
   paths to extracted services.
2. Move state behind repositories before moving route handlers into separate
   processes.
3. Replace local JSON files with a service-owned database model before scaling
   a service horizontally.
4. Replace local filesystem paths with object IDs or signed URLs before moving
   media generation into workers.
5. Treat WebSocket progress streams as a gateway concern backed by Redis Pub/Sub
   or a message broker, not as direct worker connections.

## Extraction Status

1. `identity`: keep account/session mutations isolated in the identity service;
   boundary services validate tokens remotely through `/auth/internal/resolve`.
2. `asset-library`: owns upload metadata and object storage. Existing feature
   routes keep legacy file fields but resolve material text by object key.
3. `ai-core`: owns LLM provider invocation and isolates provider credentials
   from feature services through `/ai/internal/invoke`.
4. `media-generation`: owns TTS, speech evaluation, Podcast, Speaking
   artifacts, and the `/api/bilibili/search` proxy. The actual Bilibili MCP
   process runs as the independent `bilibili-bridge` Node service in Compose.
5. `learning-content` and `teaching-content`: own their KV records and publish
   progress through EventBus. Long-running generation work now moves through
   the queue-backed worker boundary, and websocket delivery no longer depends
   on process-local connection tables.

## Remaining Operational Work

- `utils.auth_db` still uses SQLite for identity-owned account/session state in
  local mode. Lightweight auth contracts live in `utils.auth_contracts`, and
  boundary routes import those contracts instead of importing the SQLite module
  for type hints. `utils.auth` lazy-loads the local auth store only when token
  validation runs in local mode; boundary services should run with
  `AUTH_VALIDATION_MODE=remote` and resolve users through the identity service.
- Local JSON and filesystem storage remain available for developer mode.
  Production rollout should run the dry-run migration report first, then run
  `scripts/migrate_storage_to_adapters.py --write` against the configured
  PostgreSQL and MinIO/S3 providers before switching an existing deployment.
- Some media utilities still use local working files while generating PDFs,
  PPTX, TTS audio, or videos. Final upload/download paths now go through
  ObjectStore, and S3 path caching supports parsers that still require a local
  file.
- User-facing long-running workflows now have a queue-backed worker boundary in
  Compose with acknowledgment, retry, and dead-letter semantics. A later scale
  upgrade can swap the adapter to Redis Streams, Celery, Dramatiq, or a cloud
  queue without changing route code.

The critical migration boundaries are now implemented: service-scoped apps,
gateway routing, remote auth validation, AI Core, PostgreSQL KV, shared
ObjectStore adapters, Redis Pub/Sub progress streams, queue-backed generation
workers with ack/retry/DLQ handling, independent Bilibili Bridge, gateway
readiness, and dry-run-first storage migration tooling.

## Verification

The route and gateway contracts are guarded by `tests/backend/test_app_factory.py`.
Any change to route registration or gateway routing should update the test
intentionally.
