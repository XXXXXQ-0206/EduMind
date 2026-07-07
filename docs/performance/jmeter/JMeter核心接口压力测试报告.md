# EduMind 核心接口 JMeter 压力测试报告

测试日期：2026-07-03  
测试对象：EduMind API Gateway `http://localhost:5000`  
JMeter HTML 报告：[html-report/index.html](html-report/index.html)  
JMeter 测试计划：[edumind-core-api-pressure.jmx](edumind-core-api-pressure.jmx)  
原始结果文件：[results/core-api-pressure.jtl](results/core-api-pressure.jtl)

## 1. 测试目标

本次只选取用户更可能直接、高频访问的核心接口进行压力测试，重点观察认证态校验、资料库列表、学习记录列表、知识卡片列表和错题本汇总等页面型读取接口在并发访问下的稳定性与响应时间。

未纳入本次压测的接口包括：大模型生成类接口、文件上传与 RAG 索引重建、删除/修改类接口、WebSocket/SSE 长连接接口。原因是这些接口更容易受外部模型、队列、对象存储或长任务执行时间影响，不适合作为本次“高频直接访问接口”的核心基线。

## 2. 核心接口范围

| 序号 | 接口 | 方法 | 纳入原因 |
|---:|---|---|---|
| 0 | `/auth/login` | POST | 每个虚拟用户登录一次，用于获取 Bearer Token |
| 1 | `/auth/me` | GET | 前端登录态校验与用户信息刷新高频调用 |
| 2 | `/files?role=student` | GET | 学生资料库入口，页面打开与刷新高频调用 |
| 3 | `/chats?role=student` | GET | 对话历史列表，学习入口高频调用 |
| 4 | `/quizzes?role=student` | GET | 测验历史列表，学习记录高频调用 |
| 5 | `/flashcards` | GET | 知识卡片列表，复习页面高频调用 |
| 6 | `/wrongbook/summary` | GET | 错题本首页汇总，高频读取且有一定聚合计算 |

## 3. 测试环境与策略

| 项目 | 配置 |
|---|---|
| 后端运行方式 | Docker Compose 启动 API Gateway、identity、learning-content、asset-library、ai-core、media-generation、teaching-content、PostgreSQL、Redis |
| JMeter 运行方式 | Docker 镜像 `justb4/jmeter:latest` 非 GUI 模式 |
| 并发线程数 | 30 |
| 升压时间 | 20 秒 |
| 持续时间 | 90 秒 |
| 思考时间 | 100-300 ms 随机等待 |
| 测试账号 | `jmeter_user_1` 到 `jmeter_user_30`，每个线程独立账号 |
| 账号策略说明 | 项目登录会使同一用户旧 session 失效，因此必须使用线程独立账号，避免测试脚本制造伪 401 |

## 4. JMeter HTML 报告截图

以下截图均来自 JMeter 生成的 HTML Dashboard，并通过浏览器打开本地 HTML 文件后截图得到。

### 4.1 Dashboard 总览

![JMeter Dashboard 总览](screenshots/jmeter_dashboard_overview.png)

### 4.2 Statistics 与 Errors 区域

![JMeter Statistics 表](screenshots/jmeter_statistics_table.png)

### 4.3 吞吐量趋势

![JMeter Throughput 图](screenshots/jmeter_throughput.png)

### 4.4 响应时间百分位

![JMeter Response Times 图](screenshots/jmeter_response_times.png)

### 4.5 平均响应时间趋势

![JMeter Over Time 图](screenshots/jmeter_over_time.png)

## 5. 测试结果

整体结果：

| 指标 | 结果 |
|---|---:|
| 总样本数 | 2079 |
| 失败数 | 0 |
| 错误率 | 0.00% |
| 测试时长 | 90 秒 |
| 整体吞吐量 | 23.10 requests/s |
| 平均响应时间 | 961.90 ms |
| 中位响应时间 | 1061.00 ms |
| P90 | 1303.00 ms |
| P95 | 1396.00 ms |
| P99 | 1667.60 ms |
| 最大响应时间 | 2078 ms |

分接口结果：

| 接口 | 样本数 | 错误率 | 平均(ms) | 中位(ms) | P90(ms) | P95(ms) | P99(ms) | 最大(ms) | 吞吐量(req/s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `POST /auth/login` | 30 | 0.00% | 400.70 | 275.00 | 892.30 | 958.80 | 961.00 | 961 | 1.50 |
| `GET /auth/me` | 356 | 0.00% | 572.45 | 575.00 | 889.30 | 972.05 | 1184.01 | 1208 | 3.98 |
| `GET /files?role=student` | 346 | 0.00% | 905.47 | 1018.00 | 1195.90 | 1255.65 | 1338.89 | 1388 | 3.88 |
| `GET /chats?role=student` | 342 | 0.00% | 1064.09 | 1139.50 | 1350.50 | 1464.50 | 1781.97 | 2036 | 3.85 |
| `GET /quizzes?role=student` | 341 | 0.00% | 1075.33 | 1127.00 | 1309.80 | 1425.70 | 1677.10 | 1862 | 3.85 |
| `GET /flashcards` | 334 | 0.00% | 1129.00 | 1167.00 | 1432.00 | 1517.50 | 2016.85 | 2078 | 3.78 |
| `GET /wrongbook/summary` | 330 | 0.00% | 1099.98 | 1141.00 | 1334.90 | 1426.90 | 1901.32 | 2059 | 3.75 |

## 6. 结论

在 30 并发、90 秒持续压测下，本次选取的核心高频接口全部通过，错误率为 0.00%，说明当前 Docker Compose 运行形态下的 API Gateway、认证服务、学习内容服务、资料库服务和 PostgreSQL/Redis 基础依赖在该压力级别下保持稳定。

响应时间方面，`/auth/me` 相对较快，平均约 572 ms；列表与汇总类接口平均约 0.9-1.13 秒，P95 约 1.25-1.52 秒。`/flashcards` 和 `/wrongbook/summary` 的尾部延迟最高，最大值超过 2 秒，后续可重点检查认证解析、跨服务调用、PostgreSQL KV 前缀扫描、列表分页和缓存策略。

## 7. 复现命令

```powershell
docker compose up -d api-gateway

docker run --rm `
  --mount "type=bind,source=$PWD,target=/work" `
  justb4/jmeter:latest `
  -n `
  -t /work/docs/performance/jmeter/edumind-core-api-pressure.jmx `
  -l /work/docs/performance/jmeter/results/core-api-pressure.jtl `
  -e `
  -o /work/docs/performance/jmeter/html-report `
  -Jhost=host.docker.internal `
  -Jport=5000 `
  -Jthreads=30 `
  -Jramp=20 `
  -Jduration=90 `
  -JusernamePrefix=jmeter_user_ `
  -Jpassword=jmeter123
```
