# SQLite / JSON 到 PostgreSQL + pgvector 改造说明

这份 README 说明 EduMind 将 SQLite / JSON 文件存储改为 PostgreSQL + pgvector 后，系统在数据持久化、向量检索、部署协作和扩展能力上的变化与优势。

## 改造背景

改造前，项目里有两类典型本地存储：

- SQLite：主要用于 identity 账户、会话和部分聊天持久化。
- JSON 文件：用于业务元数据、生成任务状态、历史记录、文件列表、以及早期向量数据。

这种方案适合单机开发和早期验证，但在 Docker Compose、微服务拆分、多人协作和跨机器部署时会暴露问题：

- 多个服务进程同时读写本地文件，容易出现一致性和并发问题。
- 本地 `storage/` 目录和 SQLite 文件不适合在多容器之间共享。
- JSON 文件只能做简单 key-value 读取，缺少事务、索引和查询能力。
- 向量数据放在 JSON 中时，只能在应用进程内加载后用 Python / numpy 计算相似度。
- 数据迁移、备份、回滚和生产运维都缺少统一入口。

因此本次将主运行时数据层改为 PostgreSQL，并使用 pgvector 承担向量存储和相似度检索。

## 改造前

### 存储形态

```text
identity 账户 / 会话
  -> storage/edumind.sqlite3

业务状态 / 历史记录 / 任务元数据
  -> storage/*.json

向量数据
  -> storage/vectors_*.json
  -> 应用进程读取 JSON
  -> numpy 计算相似度
```

### 主要特点

| 能力 | 改造前 |
| --- | --- |
| 账户库 | SQLite 文件 |
| KV 状态 | JSON 文件 |
| 向量存储 | JSON 文件中的数组 |
| 向量检索 | 应用进程内计算 |
| 并发写入 | 依赖文件锁 / 进程内锁，跨进程能力弱 |
| 查询能力 | 主要按文件名或 key 获取 |
| 部署方式 | 更适合单机本地开发 |
| 数据运维 | 备份和迁移依赖拷贝文件 |

### 典型问题

```text
多个服务实例
  -> 同时访问本地 storage 目录
  -> JSON / SQLite 文件难以跨容器可靠共享
  -> 查询、索引、事务能力不足
```

向量检索也存在类似问题：

```text
读取 vectors_xxx.json
  -> 把所有向量加载到 Python 内存
  -> numpy 计算余弦相似度
  -> 数据量增大后内存和 CPU 压力变高
```

## 改造后

### 存储形态

```text
identity 账户 / 会话
  -> PostgreSQL auth_* tables

业务状态 / 历史记录 / 任务元数据
  -> PostgreSQL JSONB KV table

向量数据
  -> PostgreSQL + pgvector
  -> edumind_vectors table
  -> SQL 中使用 pgvector 距离算子排序
```

### 主要特点

| 能力 | 改造后 |
| --- | --- |
| 账户库 | PostgreSQL 表 |
| KV 状态 | PostgreSQL JSONB |
| 向量存储 | pgvector `vector` 列 |
| 向量检索 | PostgreSQL 内部执行相似度排序 |
| 并发写入 | 数据库事务和行级锁 |
| 查询能力 | SQL、索引、JSONB、排序、过滤 |
| 部署方式 | 适合 Docker Compose / 多服务 / 多 worker |
| 数据运维 | 统一用 PostgreSQL 备份、恢复、迁移 |

新的整体结构：

```text
API / service / worker
  -> PostgreSQL
      -> auth_users / auth_sessions / auth_chats / auth_chat_messages
      -> edumind_kv(value jsonb)
      -> edumind_vectors(embedding vector)
```

## 核心变化

### 1. Identity 从 SQLite 改为 PostgreSQL

改造前：

```text
utils/auth_db.py
  -> sqlite3.connect(storage/edumind.sqlite3)
  -> users / sessions / chats / chat_messages
```

改造后：

```text
utils/auth_db.py
  -> psycopg.connect(POSTGRES_DSN)
  -> auth_users / auth_sessions / auth_chats / auth_chat_messages
```

优势：

- 账户和会话不再绑定单机文件。
- identity 服务可以稳定服务多个业务边界。
- 数据库事务保证注册、登录、改密、删除会话等操作更可靠。
- 后续可以平滑增加 migration、审计字段、索引和权限控制。

旧 SQLite 文件不再作为运行时数据库，只作为启动迁移来源：

```text
storage/edumind.sqlite3
  -> startup migration
  -> PostgreSQL auth tables
```

### 2. JSONStorage API 保留，底层改为 PostgreSQL JSONB

业务代码里大量地方仍然调用：

```python
await json_storage.get(key)
await json_storage.set(key, value)
await json_storage.update(key, updater)
await json_storage.list_prefix(prefix)
```

改造没有强迫所有业务路由一次性重写，而是保留原有 API，把底层 provider 从 JSON 文件切到 PostgreSQL JSONB。

改造前：

```text
json_storage.set("quiz:xxx", data)
  -> storage/quiz_xxx.json
```

改造后：

```text
json_storage.set("quiz:xxx", data)
  -> edumind_kv(key text primary key, value jsonb)
```

优势：

- 调用方改动小，迁移风险低。
- JSONB 仍然保留灵活结构，适合生成类业务快速迭代。
- PostgreSQL 提供事务和并发控制。
- 后续可以逐步把高频业务从 KV 表拆成正式关系表。

### 3. 向量存储从 JSON / numpy 改为 pgvector

改造前：

```text
VectorStore.add_documents()
  -> embeddings.aembed_documents(texts)
  -> 保存 texts / vectors / metadatas 到 JSON

VectorStore.similarity_search()
  -> 读取整个 JSON
  -> numpy 计算余弦相似度
  -> 应用进程排序 top-k
```

改造后：

```text
VectorStore.add_documents()
  -> embeddings.aembed_documents(texts)
  -> INSERT INTO edumind_vectors(..., embedding vector)

VectorStore.similarity_search()
  -> 生成 query embedding
  -> ORDER BY embedding <=> query_vector
  -> PostgreSQL 返回 top-k
```

优势：

- 向量数据进入数据库统一管理。
- 检索逻辑下沉到 PostgreSQL，不需要每次把全部向量加载进应用内存。
- 后续可以增加 HNSW / IVFFlat 等 pgvector 索引策略。
- metadata 使用 JSONB，仍可保留来源、文件、页码、业务标签等灵活信息。

### 4. Docker Compose 使用 pgvector 镜像

改造前：

```yaml
postgres:
  image: postgres:16-alpine
```

改造后：

```yaml
postgres:
  image: pgvector/pgvector:pg16
```

应用启动时会执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

这保证 PostgreSQL 具备 `vector` 类型和 pgvector 距离算子。

## 配置变化

推荐配置：

```env
db_mode=postgres
KV_STORE_PROVIDER=postgres
POSTGRES_DSN=postgresql://edumind:edumind@postgres:5432/edumind
VECTOR_STORE_PROVIDER=pgvector
PGVECTOR_TABLE=edumind_vectors
```

相关基础设施：

```env
POSTGRES_DB=edumind
POSTGRES_USER=edumind
POSTGRES_PASSWORD=edumind
```

## 迁移路径

### SQLite 账户数据

启动 identity / monolith 时会尝试读取旧文件：

```text
storage/edumind.sqlite3
storage/pagelm.sqlite3
```

如果旧库存在，会导入到 PostgreSQL auth 表中。

### JSON KV 数据

旧 JSON 文件可以通过迁移脚本导入 PostgreSQL KV：

```powershell
python scripts/migrate_storage_to_adapters.py --source-dir storage
python scripts/migrate_storage_to_adapters.py --source-dir storage --write
```

默认 dry-run，确认扫描结果后再加 `--write`。

### JSON 向量数据

旧的：

```text
storage/vectors_*.json
```

现在会作为 legacy vector 数据迁移到 pgvector，而不是继续写入普通 KV。

## 前后对比总览

| 维度 | 改造前 | 改造后 |
| --- | --- | --- |
| 账户数据 | SQLite 文件 | PostgreSQL auth tables |
| 业务状态 | JSON 文件 | PostgreSQL JSONB KV |
| 向量数据 | JSON 数组 | pgvector `vector` 列 |
| 相似度计算 | Python / numpy | PostgreSQL / pgvector |
| 并发能力 | 单机友好，跨进程弱 | 数据库事务和锁 |
| 微服务适配 | 本地文件共享困难 | 多服务共享同一 DB |
| 运维方式 | 拷贝文件 | 数据库备份/恢复/迁移 |
| 扩展能力 | 难做索引和查询 | SQL、JSONB、vector index |
| 回滚与兼容 | 直接读旧文件 | 旧文件作为迁移来源 |

## 主要优势

### 1. 更适合微服务部署

多个服务和 worker 不再依赖本地文件路径。只要连接同一个 PostgreSQL，就能共享账户、任务状态、历史记录和向量数据。

### 2. 数据一致性更好

PostgreSQL 提供事务、约束、锁和并发控制。相比多个进程写 JSON 文件，风险更低。

### 3. 查询和排障更方便

可以直接用 SQL 查看状态：

```sql
SELECT key, updated_at
FROM edumind_kv
ORDER BY updated_at DESC;
```

也可以检查向量数据：

```sql
SELECT namespace, count(*)
FROM edumind_vectors
GROUP BY namespace;
```

### 4. 向量检索更可扩展

pgvector 让向量成为数据库原生字段。当前可以先用精确相似度排序，后续数据量变大后再增加 ANN 索引。

### 5. 迁移风险更低

业务层的 `JSONStorage` API 保留，调用方不用一次性全部改成关系模型。旧 SQLite / JSON 数据也保留迁移入口。

## 注意事项

- 运行时需要使用带 pgvector 扩展的 PostgreSQL 镜像。
- `POSTGRES_DSN` 在 Docker Compose 内应使用 `postgres` 作为 host。
- 如果在宿主机本地直连，需要把 host 改成实际可访问地址，例如 `localhost`。
- JSON 文件和 SQLite 文件不再是推荐运行时存储，只作为迁移和本地调试来源。
- pgvector 索引策略可以后续按数据量和 embedding 维度继续优化。

## 总结

这次改造的核心是把 EduMind 的数据底座从本地文件模式升级为数据库模式：

```text
SQLite / JSON files
  -> PostgreSQL JSONB + PostgreSQL auth tables + pgvector
```

最终收益是：

- 账户、业务状态和向量数据统一进入 PostgreSQL。
- 微服务和 worker 可以共享稳定数据源。
- 并发、事务、查询、备份、迁移能力显著增强。
- 向量检索从应用内计算升级为数据库内 pgvector 检索。
- 保留旧数据迁移路径，降低切换风险。
