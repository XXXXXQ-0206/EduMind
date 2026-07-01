# EduMind Environment Setup Guide For Agents

This repository now runs as a Docker Compose based microservice topology. The
old local-only fast start path is intentionally removed. Use this guide when
configuring a fresh machine or repairing a broken environment.

## Current Runtime Shape

The expected root directory is:

```text
C:\Users\<user>\Desktop\EduMind
```

Required top-level entries:

- `docker-compose.yml`
- `backend\`
- `frontend\`
- `services\bilibili-mcp\`
- `deploy\docker\`
- `setup-edumind-environment.ps1`
- `start-edumind.ps1`

On a new machine, run the environment setup first:

```powershell
.\setup-edumind-environment.ps1
```

This script installs/checks Docker Desktop, starts the Docker daemon, validates
Compose, creates `.env` from `.env.example` if needed, and builds
the Docker images. After setup completes, daily startup is:

```powershell
.\start-edumind.ps1
```

The quick start script assumes setup has already completed. It starts Docker
Desktop when needed and runs the full Docker Compose topology without rebuilding
images by default.

## Required Host Software

Install these before running the app:

- Docker Desktop for Windows, with Docker Compose v2.
- Git, if the machine needs to clone or update the repository.
- PowerShell 5+ or PowerShell 7+.

Python and Node do not need to be installed on the host for the normal Docker
startup path. They are installed inside the backend/frontend images. Host Python
is only useful for local test/debug workflows.

`setup-edumind-environment.ps1` can install Docker Desktop through `winget` when
Docker is missing. If Docker Desktop asks for WSL2 setup or a reboot, complete
that system step and rerun the setup script.

## Docker Requirements

Docker Desktop must be able to run Linux containers. If startup fails with a
daemon or pipe error, start Docker Desktop manually once and wait until it says
Docker is running.

Useful checks:

```powershell
docker compose version
docker info
docker compose config --quiet
docker compose config --services
```

Expected services include:

- `postgres`
- `redis`
- `minio`
- `minio-init`
- `identity`
- `learning-content`
- `asset-library`
- `ai-core`
- `bilibili-bridge`
- `media-generation`
- `teaching-content`
- `generation-worker`
- `api-gateway`
- `frontend`

## Build Mirrors And Overrides

The Compose build defaults are tuned for the current Windows/China network
environment. They avoid direct Docker Hub and public package registry access
where possible:

```text
DOCKER_NODE_IMAGE=docker.1ms.run/library/node:20-alpine
DOCKER_PYTHON_IMAGE=dockerproxy.net/library/python:3.11-slim-bookworm
DOCKER_NGINX_IMAGE=dockerproxy.net/library/nginx:1.27-alpine
DEBIAN_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian
NODE_VERSION=20.20.2
NPM_REGISTRY=https://registry.npmmirror.com
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

Override these only when a mirror is unavailable on the target machine. Example:

```powershell
$env:DOCKER_PYTHON_IMAGE = "python:3.11-slim-bookworm"
$env:PIP_INDEX_URL = "https://pypi.org/simple"
.\setup-edumind-environment.ps1
```

## Environment File

The Compose file reads:

```text
.env
```

If it is missing, copy:

```powershell
Copy-Item .\.env.example .\.env
```

Then fill API keys as needed. The app can start without every provider key, but
AI features fail when the selected provider key is missing.

Important variables:

```text
LLM_PROVIDER=gemini
gemini=<real key>
OPENAI_API_KEY=<real key if using OpenAI>
OPENAI_EMBED_API_KEY=<real key if using OpenAI embeddings>
DEEPSEEK_API_KEY=<real key if using DeepSeek or podcast defaults>
```

Microservice infrastructure defaults are controlled by `docker-compose.yml`:

```text
KV_STORE_PROVIDER=postgres
POSTGRES_DSN=postgresql://edumind:edumind@postgres:5432/edumind
EVENT_BUS_PROVIDER=redis
TASK_QUEUE_PROVIDER=redis
OBJECT_STORE_PROVIDER=s3
AI_CORE_URL=http://ai-core:5106
BILIBILI_BRIDGE_URL=http://bilibili-bridge:5001
```

Do not change these unless intentionally debugging a service boundary.

## Standard Commands

New-machine setup check without installing/building:

```powershell
.\setup-edumind-environment.ps1 -CheckOnly
```

New-machine setup:

```powershell
.\setup-edumind-environment.ps1
```

Daily quick-start check:

```powershell
.\start-edumind.ps1 -CheckOnly
```

Daily quick start:

```powershell
.\start-edumind.ps1
```

Quick start with a rebuild:

```powershell
.\start-edumind.ps1 -Build
```

Follow important logs after startup:

```powershell
.\start-edumind.ps1 -Logs
```

Manual Compose equivalents:

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f api-gateway ai-core generation-worker bilibili-bridge
docker compose down
```

## Health URLs

After startup:

- Frontend: `http://localhost`
- API Gateway: `http://localhost:5000`
- Gateway readiness: `http://localhost:5000/health/ready`
- MinIO console: `http://localhost:9001`

Gateway readiness can stay `503` while backend services are still booting. Use:

```powershell
docker compose ps
docker compose logs -f api-gateway
```

## Data And Volumes

Compose creates named volumes:

- `postgres-data`
- `minio-data`

Do not delete these unless resetting local state is intentional.

Local bind mounts still exist for development compatibility:

- `.\storage`
- `.\models`

## Migration Notes

The current backend is microservice-oriented:

- `api-gateway` exposes the old public API paths.
- `ai-core` owns direct LLM provider calls.
- `bilibili-bridge` is an independent Node service.
- `generation-worker` consumes Redis queue tasks.
- PostgreSQL stores KV JSONB records.
- Redis handles events, leases, and queue semantics.
- MinIO stores generated/uploaded objects.

Avoid starting `backend\main.py` directly as the primary app on a new machine.
That path is only for narrow local debugging and does not represent the current
full deployment topology.
