# EduMind 新机器环境配置指南（给 Agent）

本文给接手项目的 agent 或开发者使用。当前版本不再维护“不拉 Docker 的快速启动路径”；新机器先运行环境配置脚本，再运行快速启动脚本。

## 当前运行形态

项目根目录应直接是：

```text
C:\Users\<user>\Desktop\EduMind
```

根目录必须包含：

- `docker-compose.yml`
- `backend\`
- `frontend\`
- `services\bilibili-mcp\`
- `deploy\docker\`
- `setup-edumind-environment.ps1`
- `start-edumind.ps1`

正常流程：

```powershell
.\setup-edumind-environment.ps1
.\start-edumind.ps1
```

`setup-edumind-environment.ps1` 用于新机器配置：检查或安装 Git、Docker Desktop，启动 Docker daemon，创建 `.env`，校验 Compose 拓扑，并构建后端和前端镜像。

`start-edumind.ps1` 用于日常启动：假设环境配置已经完成，负责启动 Docker Desktop 和完整 Docker Compose 微服务拓扑，默认不重新构建镜像。

## 主机依赖

日常 Docker 启动只要求主机具备：

- Docker Desktop for Windows，包含 Docker Compose v2。
- Git，用于克隆和更新仓库。
- PowerShell 5+ 或 PowerShell 7+。

Python、Node、后端依赖、前端依赖和 Bilibili MCP 依赖都安装在 Docker 镜像内。只有做本地调试或直接跑测试时，才需要主机 Python / Node。

如果 Docker Desktop 提示需要 WSL2 或重启，按系统提示完成后重新运行：

```powershell
.\setup-edumind-environment.ps1
```

## Compose 服务清单

当前 Compose 拓扑应包含：

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

检查命令：

```powershell
docker compose config --quiet
docker compose config --services
```

## 镜像源和构建参数

脚本默认使用适合 Windows / 国内网络的镜像和包源：

```text
DOCKER_NODE_IMAGE=docker.1ms.run/library/node:20-alpine
DOCKER_PYTHON_IMAGE=dockerproxy.net/library/python:3.11-slim-bookworm
DOCKER_NGINX_IMAGE=dockerproxy.net/library/nginx:1.27-alpine
DEBIAN_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian
NODE_VERSION=20.20.2
NPM_REGISTRY=https://registry.npmmirror.com
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

目标机器如果访问这些镜像源失败，可以临时覆盖：

```powershell
$env:DOCKER_PYTHON_IMAGE = "python:3.11-slim-bookworm"
$env:PIP_INDEX_URL = "https://pypi.org/simple"
.\setup-edumind-environment.ps1
```

## `.env` 配置

脚本会在缺失 `.env` 时从 `.env.example` 复制：

```powershell
Copy-Item .\.env.example .\.env
```

启动前检查并补充模型、TTS、讯飞、即梦等密钥。应用可以在缺少部分 provider 密钥时启动，但对应 AI 功能会失败或降级。

常用模型变量：

```text
LLM_PROVIDER=gemini
gemini=<real key>
OPENAI_API_KEY=<real key if using OpenAI>
OPENAI_EMBED_API_KEY=<real key if using OpenAI embeddings>
DEEPSEEK_API_KEY=<real key if using DeepSeek or podcast defaults>
```

Compose 会给服务注入以下默认基础设施配置，通常不要在新机器上改动：

```text
KV_STORE_PROVIDER=postgres
POSTGRES_DSN=postgresql://edumind:edumind@postgres:5432/edumind
OBJECT_STORE_PROVIDER=s3
EVENT_BUS_PROVIDER=redis
TASK_QUEUE_PROVIDER=redis
TASK_LEASE_PROVIDER=redis
AI_CORE_URL=http://ai-core:5106
BILIBILI_BRIDGE_URL=http://bilibili-bridge:5001
```

## 标准命令

只检查新机器环境，不安装、不构建：

```powershell
.\setup-edumind-environment.ps1 -CheckOnly
```

配置新机器：

```powershell
.\setup-edumind-environment.ps1
```

日常启动前检查：

```powershell
.\start-edumind.ps1 -CheckOnly
```

日常启动：

```powershell
.\start-edumind.ps1
```

启动时强制重新构建镜像：

```powershell
.\start-edumind.ps1 -Build
```

启动并跟随关键日志：

```powershell
.\start-edumind.ps1 -Logs
```

常用 Docker 命令：

```powershell
docker compose ps
docker compose logs -f api-gateway ai-core generation-worker bilibili-bridge
docker compose down
docker compose down -v
```

`docker compose down -v` 会删除 PostgreSQL 和 MinIO volume，只能在明确要重置本机数据时使用。

## 健康检查

启动后访问：

- 前端：`http://localhost`
- API Gateway：`http://localhost:5000`
- Gateway readiness：`http://localhost:5000/health/ready`
- MinIO 控制台：`http://localhost:9001`

`/health/ready` 在后端服务启动过程中可能短暂返回 `503`。排查时先看：

```powershell
docker compose ps
docker compose logs -f api-gateway
```

## 数据和卷

Compose 创建命名卷：

- `postgres-data`
- `minio-data`

本地兼容挂载：

- `.\storage`
- `.\models`

不要把 `.env`、`storage\`、`models\`、日志、截图或依赖目录提交到 Git。

## 架构要点

- `api-gateway` 保持旧前端路径兼容。
- `identity` 持有账户和会话；其他服务远程解析 token。
- `ai-core` 负责直接调用 LLM / Embedding provider。
- `generation-worker` 消费 Redis 队列中的长任务。
- `bilibili-bridge` 是独立 Node 服务，连接 `services/bilibili-mcp`。
- PostgreSQL 保存 KV JSONB 状态。
- Redis 处理事件、租约和任务队列。
- MinIO 保存上传文件和生成对象。

不要把 `backend\main.py` 当作新机器的主启动方式。它只保留给本地排障和兼容旧数据迁移。
