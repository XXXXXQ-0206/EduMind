# PageLM 华为云 ECS Docker 部署指南

本文档针对华为云 ECS（Ubuntu/CentOS 均适用）部署，已吸收你提到的常见坑：磁盘不足、镜像拉取慢、HF 下载失败、端口不通。

## 1. 服务器准备

1. 安装 Docker 和 Docker Compose 插件。
2. 检查磁盘空间（建议至少 40GB 可用，推荐 60GB+）。
3. 开放华为云安全组入站端口：
   1. TCP 80（前端）
   2. TCP 5000（后端 API / WebSocket）

## 2. 配置 Docker 镜像加速（华为云 SWR）

编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://<你的SWR加速地址>"
  ]
}
```

重启 Docker：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
docker info | grep -i "Registry Mirrors" -A 5
```

## 3. 上传代码并进入项目目录

假设代码目录为：

```bash
cd LinkEdu-main-version1
```

此目录下应至少存在：

- `docker-compose.yml`
- `PageLM-main/`
- `bilibili-mcp-js-main/`

## 4. 配置后端环境变量

复制并编辑后端 `.env`：

```bash
cp PageLM-main/.env.example PageLM-main/.env
```

至少确认以下项：

```bash
HOST=0.0.0.0
PORT=5000
VITE_BACKEND_URL=http://<你的ECS公网IP>:5000
HF_ENDPOINT=https://hf-mirror.com
```

说明：

- `VITE_BACKEND_URL` 同时用于前端构建注入（见第 5 步）。
- `HF_ENDPOINT` 可以降低模型下载失败概率。

## 5. 构建并启动容器

首次部署建议明确传入前端构建参数：

```bash
VITE_BACKEND_URL=http://<你的ECS公网IP>:5000 \
HF_ENDPOINT=https://hf-mirror.com \
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs -f backend
```

访问：

- 前端：`http://<你的ECS公网IP>/`
- 后端健康检查：`http://<你的ECS公网IP>:5000/health`

## 6. 常见问题处理

### 6.1 `no space left on device`

```bash
docker system df
docker system prune -a
docker builder prune -a
```

如果还不够：

1. 增加云盘容量。
2. 清理旧镜像和无用容器。
3. 避免把临时大文件放入构建上下文。

### 6.2 拉取镜像慢/超时

1. 确认 SWR 镜像加速已生效。
2. 重试构建：`docker compose build --no-cache`。

### 6.3 Hugging Face 下载失败

确保后端容器内存在：

```bash
HF_ENDPOINT=https://hf-mirror.com
```

可用命令验证：

```bash
docker compose exec backend env | grep HF_ENDPOINT
```

### 6.4 容器是 Up 但网页打不开

1. 安全组是否放行 TCP 80、5000。
2. ECS 本机防火墙是否拦截（如 `ufw` / `firewalld`）。
3. 端口映射是否正确（`docker compose ps` 检查 `0.0.0.0:80->80/tcp`）。

### 6.5 B 站 MCP 功能不可用

后端启动会自动拉起 Node bridge；若异常，先看日志：

```bash
docker compose logs -f backend
```

已在镜像中预编译 `bilibili-mcp-js-main/dist/index.js`，并通过 `BILIBILI_MCP_ENTRY` 指向容器内路径。

## 7. 更新部署

代码更新后：

```bash
git pull
VITE_BACKEND_URL=http://<你的ECS公网IP>:5000 docker compose up -d --build
```

## 8. 回滚（快速）

```bash
docker compose down
```

如果你有历史镜像 tag，可以直接使用旧 tag 重新 `up -d`。
