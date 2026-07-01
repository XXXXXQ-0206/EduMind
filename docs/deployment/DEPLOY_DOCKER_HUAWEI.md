# EduMind 华为云 ECS Docker 部署指南

本文用于把当前 EduMind 微服务版本部署到华为云 ECS。部署形态为 Docker Compose：前端 Nginx、API Gateway、6 个后端边界服务、generation-worker、Bilibili Bridge、PostgreSQL、Redis 和 MinIO。

## 1. 服务器准备

建议配置：

- Linux ECS，Ubuntu 22.04 / 24.04 或 CentOS 系均可。
- 2 vCPU / 4GB 内存起步；生成视频、语音或大量并发时建议更高。
- 至少 40GB 可用磁盘，推荐 60GB+。
- 已安装 Docker Engine 和 Docker Compose v2 插件。

安全组放行：

- TCP 80：前端。
- TCP 5000：API Gateway / WebSocket。
- 可选 TCP 9001：MinIO 控制台，仅限受信任 IP。

检查：

```bash
docker compose version
docker info
df -h
```

## 2. 配置 Docker 镜像加速

如果拉取镜像慢，配置华为云 SWR 或可用镜像源：

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json >/dev/null <<'JSON'
{
  "registry-mirrors": [
    "https://<你的SWR加速地址>"
  ]
}
JSON

sudo systemctl daemon-reload
sudo systemctl restart docker
docker info | grep -i "Registry Mirrors" -A 5
```

项目也支持通过环境变量切换基础镜像和包源：

```bash
export DOCKER_PYTHON_IMAGE=python:3.11-slim-bookworm
export DOCKER_NODE_IMAGE=node:20-alpine
export DOCKER_NGINX_IMAGE=nginx:1.27-alpine
export PIP_INDEX_URL=https://pypi.org/simple
export NPM_REGISTRY=https://registry.npmjs.org
```

## 3. 上传代码并进入项目目录

项目根目录应直接包含：

- `docker-compose.yml`
- `backend/`
- `frontend/`
- `services/bilibili-mcp/`
- `deploy/docker/`
- `.env.example`

示例：

```bash
git clone https://github.com/XXXXXQ-0206/EduMind.git
cd EduMind
```

## 4. 配置环境变量

复制模板：

```bash
cp ./.env.example ./.env
```

至少确认：

```bash
HOST=0.0.0.0
PORT=5000
VITE_BACKEND_URL=http://<你的ECS公网IP>:5000
OBJECT_STORE_BASE_URL=http://<你的ECS公网IP>:9000/edumind
HF_ENDPOINT=https://hf-mirror.com
```

根据实际模型供应商补充密钥，例如：

```bash
LLM_PROVIDER=gemini
gemini=<real key>
OPENAI_API_KEY=<real key>
OPENAI_EMBED_API_KEY=<real key>
DEEPSEEK_API_KEY=<real key>
```

Compose 默认会注入微服务基础设施配置：

```bash
KV_STORE_PROVIDER=postgres
VECTOR_STORE_PROVIDER=pgvector
PGVECTOR_TABLE=edumind_vectors
OBJECT_STORE_PROVIDER=s3
EVENT_BUS_PROVIDER=redis
TASK_QUEUE_PROVIDER=celery
TASK_LEASE_PROVIDER=redis
AI_CORE_URL=http://ai-core:5106
BILIBILI_BRIDGE_URL=http://bilibili-bridge:5001
```

除非明确排障，不要把这些值改成本地 JSON、local object store 或 inline queue。

## 5. 构建并启动

首次部署：

```bash
VITE_BACKEND_URL=http://<你的ECS公网IP>:5000 \
HF_ENDPOINT=https://hf-mirror.com \
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs -f api-gateway ai-core generation-worker bilibili-bridge
```

访问：

- 前端：`http://<你的ECS公网IP>/`
- Gateway readiness：`http://<你的ECS公网IP>:5000/health/ready`
- MinIO 控制台：`http://<你的ECS公网IP>:9001`

## 6. 数据和备份

Compose 使用命名卷：

- `postgres-data`：KV 状态和业务元数据。
- `minio-data`：上传文件和生成对象。

备份前先确认卷名：

```bash
docker volume ls | grep edumind
```

不要随意执行：

```bash
docker compose down -v
```

该命令会删除 PostgreSQL 和 MinIO 数据卷，只适合重置测试环境。

旧本地 `storage/` 数据迁移到当前适配器时，先 dry-run：

```bash
python scripts/migrate_storage_to_adapters.py --source-dir storage
python scripts/migrate_storage_to_adapters.py --source-dir storage --write
```

## 7. 常见问题

### 7.1 `no space left on device`

```bash
docker system df
docker system prune -a
docker builder prune -a
df -h
```

仍不足时，扩容云盘或清理旧镜像和无用容器。

### 7.2 拉取镜像慢或超时

1. 确认 Docker registry mirror 生效。
2. 切换 `DOCKER_PYTHON_IMAGE`、`DOCKER_NODE_IMAGE`、`DOCKER_NGINX_IMAGE`。
3. 重试：

```bash
docker compose build --no-cache
```

### 7.3 Hugging Face 下载失败

确认容器内有：

```bash
docker compose exec api-gateway env | grep HF_ENDPOINT
```

推荐：

```bash
HF_ENDPOINT=https://hf-mirror.com
```

### 7.4 容器 Up 但页面打不开

检查：

```bash
docker compose ps
curl -I http://127.0.0.1
curl -I http://127.0.0.1:5000/health/ready
```

再确认安全组、防火墙和端口映射。常见端口应包含：

- `0.0.0.0:80->80/tcp`
- `0.0.0.0:5000->5000/tcp`

### 7.5 Gateway readiness 返回 `503`

查看各服务健康状态：

```bash
docker compose ps
docker compose logs -f identity learning-content asset-library ai-core media-generation teaching-content
```

`api-gateway` 只有在所有上游 `/health` 正常后才会 ready。

### 7.6 生成文件链接仍指向 `localhost`

检查 `.env`：

```bash
grep OBJECT_STORE_BASE_URL .env
```

公网部署应设置为：

```bash
OBJECT_STORE_BASE_URL=http://<你的ECS公网IP>:9000/edumind
```

### 7.7 B 站搜索不可用

当前版本单独启动 `bilibili-bridge`。排查：

```bash
docker compose logs -f bilibili-bridge media-generation
docker compose exec bilibili-bridge node -v
```

镜像内应存在 `/app/services/bilibili-mcp/dist/index.js`，并由 `BILIBILI_MCP_ENTRY` 指向该路径。

### 7.8 AI 功能失败

先看 `ai-core`：

```bash
docker compose logs -f ai-core
docker compose exec ai-core env | grep -E "LLM_PROVIDER|OPENAI|gemini|DEEPSEEK|ANTHROPIC"
```

确认 `.env` 中对应 provider 的密钥真实可用。

## 8. 更新部署

```bash
git pull
VITE_BACKEND_URL=http://<你的ECS公网IP>:5000 \
HF_ENDPOINT=https://hf-mirror.com \
docker compose up -d --build
docker compose ps
```

## 9. 回滚和停止

停止服务但保留数据：

```bash
docker compose down
```

如果使用过镜像 tag，可切回旧 tag 后重新 `docker compose up -d`。不要用 `down -v` 做常规回滚。
