# EduMind（智教）项目技术文档 —— 面试向

本文档面向面试场景，详细说明学生端/教师端各功能实现、所用技术及项目结构与关键文件作用，便于应对“项目细节拷打”。

---

## 一、项目概览

- **定位**：师生协同的 AI 全场景教育生态平台，围绕“备课—授课—学习—复盘”构建完整链路。
- **前端**：Vue 3 + Vite + TypeScript + TailwindCSS，SPA，支持教师/学生双角色切换。
- **后端**：Python 3.10+，FastAPI，异步 IO；AI 侧使用 LangChain 封装多 LLM、嵌入与 TTS。
- **数据**：默认 JSON 文件存储（`utils/storage.py`），可选 SQLite；向量检索用嵌入+本地 JSON 或 FAISS/ChromaDB。
- **部署**：前后端分离，后端 CORS 放行前端域名；可 Docker 部署。

---

## 二、项目文件夹与主要文件作用

### 2.1 根目录

| 文件/目录 | 作用 |
|-----------|------|
| `README.md` | 项目说明、快速开始、配置说明、功能列表 |
| `knowledge.md` | 本技术文档，面试向实现细节 |
| `.env` / `.env.example` | 环境变量：LLM/TTS/即梦/讯飞等 API、端口、存储路径 |
| `logo/logo.png` | 品牌 logo，前端首页/对话欢迎区/README 展示 |
| `backend/` | Python FastAPI 后端 |
| `frontend/` | Vue 3 前端工程 |
| `storage/` | 运行时生成目录：上传文件、笔记 PDF、播客音频、幻灯片、教学视频、JSON 库等 |

### 2.2 后端 `backend/`

| 文件/目录 | 作用 |
|-----------|------|
| `main.py` | FastAPI 入口：注册 CORS、挂载 `/storage` 静态目录、注册各业务路由 |
| `config.py` | Pydantic Settings 配置：从 `.env` 读取 LLM/嵌入/TTS/即梦/讯飞/存储路径等；启动时创建 `storage` 下各子目录 |
| `api/routes/` | 各功能 HTTP + WebSocket 路由 |
| `services/` | Node MCP Bridge 服务：MCP Client 管理与 B站搜索桥接接口 |
| `agents/` | 各业务 Agent：封装 LLM 调用、Prompt、结构化输出（教案/测验/播客/幻灯片/视频脚本等） |
| `utils/` | 通用工具：LLM/嵌入封装、TTS、文档解析、存储、WebSocket 管理、即梦配图/视频 |

### 2.3 后端 `api/routes/` 各文件

| 文件 | 对应功能 | 核心接口与说明 |
|------|----------|----------------|
| `chat.py` | 对话（教师/学生） | `POST /chat` 创建会话并返回 WebSocket URL；`WS /ws/chat` 流式返回 LLM 回复；`GET/DELETE /chats` 列表与删除；按 `role` 区分教师/学生存储 |
| `files.py` | 文件库 | `GET /files` 按 role 列文件；`POST /files` 多文件上传；`DELETE /files/{id}` 删除；上传存 `storage/uploads/`，元数据写 JSON |
| `notes.py` | 智能笔记 | `POST /smartnotes` 创建并返回 WS URL；`WS /ws/smartnotes` 流式生成康奈尔笔记；支持关联资料；PDF 导出 |
| `quiz.py` | 测验 | `POST /quiz` 创建测验；`WS /ws/quiz` 流式出题；`GET/POST /quizzes/{id}/attempts` 作答与保存；错题本汇总、报告、薄弱点分析接口 |
| `podcast.py` | 播客 | `POST /podcast` 创建；`WS /ws/podcast` 流式生成脚本并 TTS 分段合成；`GET /podcast/download/{pid}/{filename}` 下载音频 |
| `flashcards.py` | 知识卡片 | `POST /flashcards/decks` 从主题/资料生成卡组；`GET/DELETE` 卡组与单卡；概念+填空+问答结构 |
| `lesson_plan.py` | 教案 | `POST /lesson-plan` 同步生成教案（Agent 返回 JSON）；`GET /lesson-plans/{id}/pdf` PDF 导出（reportlab） |
| `slides.py` | 教学幻灯片 | `POST /slides/generate` 调用 SlidesAgent（DeepSeek 大纲 + 即梦配图）；仅大纲+插图，不生成 pptx；列表与下载 |
| `teaching_video.py` | 教学视频 | `POST /teaching-video` 创建；`WS /ws/teaching-video` 脚本→即梦文生视频→Edge TTS 配音→合成 MP4；列表/流式播放/删除 |
| `paper.py` | 试卷 | `POST /paper` 创建；`WS /ws/paper` 流式生成题目；`GET /papers/{id}/pdf` 导出 PDF |
| `speaking.py` | 英语口语 | 生成题目、上传录音、讯飞 ISE 评测、历史记录 |
| `bilibili.py` | B站视频学习/备课 | `GET /api/bilibili/search?keyword=...`；FastAPI 转发到 Node MCP Bridge，返回标题/封面/BV/UP主/时长/简介 |

### 2.4 后端 `services/`（Node MCP Bridge）

| 文件 | 作用 |
|------|------|
| `mcpManager.js` | MCP Client 单例：使用 `StdioClientTransport` 连接 `services/bilibili-mcp/dist/index.js`，初始化工具并执行视频检索 |
| `bilibiliBridgeServer.js` | Node Bridge HTTP 服务：暴露 `GET /api/bilibili/search`，供 FastAPI 转发调用 |

### 2.4 后端 `agents/` 各 Agent

| Agent | 输入 | 输出 | 技术要点 |
|-------|------|------|----------|
| `base.py` | - | - | `LLMAgent` 基类：`call_llm`（LangChain）、`expect_json` 解析、流式回调 |
| `note_agent.py` | 主题 + 可选资料 | 康奈尔笔记结构化内容 | 系统 Prompt 约束格式，可流式 |
| `quiz_agent.py` | 主题/难度/题数 + 可选资料 | 题目列表（题干、选项、正确答案、解析） | 多题 JSON 或逐题流式 |
| `podcast_agent.py` | 主题 + 可选资料 | 对话式脚本段落 | 分段输出便于 TTS 按段合成 |
| `lesson_plan_agent.py` | 课题 + 可选资料 | 三维目标、重难点、准备、教学过程、作业（Pydantic 模型） | 严格 JSON 结构，便于 PDF 排版 |
| `slides_agent.py` | 主题、页数、资料 | 每页 title + bullets；配图走即梦 | DeepSeek 生成大纲，即梦生成无字配图 |
| `teaching_video_agent.py` | 主题 + 可选资料 | 纯文本讲解脚本（200–600 字） | 供即梦文生视频 + TTS 配音 |
| `paper_agent.py` | 难度、题型与数量 | 选择/填空/应用题列表 | 流式生成，reportlab 导出 PDF |
| `flashcards_agent.py` (KnowledgeCardsAgent) | 主题/资料 | 概念、问答、填空卡 | 结构化卡组 |
| `wrongbook_report_agent.py` | 错题数据 | 文字报告、强弱项、建议 | 汇总分析 |
| `speaking_agent.py` | 主题/难度 | 口语题目与参考文本 | 与讯飞评测对接 |

### 2.5 后端 `utils/` 关键模块

| 文件 | 作用 |
|------|------|
| `llm.py` | `make_llm()`：按 `LLM_PROVIDER` 创建 LangChain Chat 实例（Gemini/OpenAI/Claude/DeepSeek/Ollama/OpenRouter/Grok）；`embeddings` 嵌入模型；统一 temperature/max_tokens |
| `tts.py` | `text_to_speech(segments, output_path)`：Edge TTS / Google TTS / ElevenLabs；多段拼接用 ffmpeg 或 pydub |
| `parser.py` | `extract_text_from_file()`：PyMuPDF(DOCX)、mammoth(DOC)、TXT/MD 文本抽取，供 RAG/资料上下文 |
| `storage.py` | `JSONStorage` 异步 JSON 文件读写；`VectorStore` 向量存储（嵌入+JSON 或 FAISS）；对话/教案/测验/试卷/播客/笔记等 CRUD 与列表 |
| `websocket.py` | WebSocket 连接管理（按 chatId/quizId 等分组），`send_message` 广播到指定会话 |
| `jiemeng_video.py` / `jimeng_client.py` | 即梦（火山引擎）配图、文生视频 API 封装；教学视频流水线调用 |

### 2.6 前端 `frontend/src/` 结构

| 目录/文件 | 作用 |
|-----------|------|
| `main.ts` | 入口：创建 Vue 应用、Pinia、挂载路由 |
| `App.vue` | 根组件：侧栏/角色切换/主题切换条件渲染；`RouterView` + 过渡动画；`route.meta.hideSidebar` 时隐藏侧栏（首页/介绍页） |
| `router/index.ts` | Vue Router：`/` 首页、`/intro/teacher`、`/intro/student`、`/chat` 与 `/teacher/chat`（同一 Chat 组件）、文件库/教案/幻灯片/视频/测验/试卷/记录汇/笔记/播客/知识卡片/错题本/口语、`/bili-learning`、`/teacher/bili-learning` 等 |
| `config/env.ts` | 从 `import.meta.env` 读 `VITE_BACKEND_URL` 等，供 `lib/api` 请求后端 |
| `lib/api.ts` | 封装所有后端 API：chat/quiz/paper/notes/podcast/flashcards/files/lesson-plan/slides/teaching-video/speaking/wrongbook 等；类型定义（TypeScript 类型与接口） |
| `stores/` | Pinia：`role`（教师/学生）、`theme`、`companion` 等；角色持久化到 localStorage |
| `pages/` | 各页面组件（见下表） |
| `components/` | 公共组件：Sidebar、RoleSwitcher、ThemeToggle、Chat/Composer/MarkdownView、各功能 HistoryPanel/TopicBar 等 |

### 2.7 前端 `pages/` 与路由对应

| 页面 | 路由 | 说明 |
|------|------|------|
| `EduMindHome.vue` | `/` | 首页：双入口按钮（教师/学生）先 setRole 再 push 对应对话页 |
| `TeacherIntro.vue` / `StudentIntro.vue` | `/intro/teacher`, `/intro/student` | 介绍页，无侧栏 |
| `Chat.vue` | `/chat`, `/teacher/chat` | 对话页；`route.path.startsWith('/teacher/')` 判教师端；WebSocket 收流式回复；学习袋/历史面板 |
| `FileLibrary.vue` | `/file-library`, `/teacher/file-library` | 文件库：上传/列表/删除/预览；教学(学习)文件夹勾选，供对话等挂载 |
| `LessonPlan.vue` | `/lesson-plan` | 教案：输入课题、选资料，POST 生成，历史列表，PDF 导出 |
| `Slides.vue` | `/slides` | 幻灯片：主题+页数+资料，生成大纲+配图，列表与下载 |
| `TeachingVideo.vue` | `/teaching-video` | 教学视频：主题+资料，WS 流式脚本→即梦视频→TTS→合成，列表与播放 |
| `BiliLearning.vue` | `/bili-learning` | 学生端 B站视频学习：关键词检索、结果卡片流、一键跳转 B站视频页 |
| `BiliLessonPrep.vue` | `/teacher/bili-learning` | 教师端 bilibili视频备课：备课关键词检索、结果筛选、跳转视频页用于课堂准备 |
| `Quiz.vue` | `/quiz`, `/teacher/quiz` | 测验：创建、WS 收题、作答、提交 attempts、错题入库；教师端仅出题/查看 |
| `Paper.vue` | `/teacher/paper` | 试卷：生成、历史、PDF 导出 |
| `TeachingRecords.vue` | `/teaching-records` | 教学记录汇：对话/教案/幻灯片/视频/测验/试卷聚合、词云与趋势 |
| `SmartNotes.vue` | `/smart-notes` | 智能笔记：主题或内容生成，WS 流式，PDF 导出 |
| `Podcast.vue` | `/podcast` | 播客：主题/资料，WS 脚本+TTS，列表与下载 |
| `KnowledgeCards.vue` | `/knowledge-cards` | 知识卡片：卡组生成与复习 |
| `WrongBook.vue` | `/wrong-book` | 错题本：汇总、报告、薄弱点、巩固练习入口 |
| `WrongBookPractice.vue` | `/wrong-book/practice` | 错题练习页 |
| `LearningRecords.vue` | `/learning-records` | 学习记录汇：对话/笔记/播客/测验/卡片聚合 |
| `EnglishSpeaking.vue` | `/english-speaking` | 英语口语：题目、录音上传、评测展示 |
| `Planner.vue` / `Tools.vue` 等 | 按路由 | 作业规划、工具聚合等 |

---

## 三、教师端功能实现细节

### 3.1 对话（教师工作台）

- **路由**：`/teacher/chat`，与 `/chat` 共用 `Chat.vue`，通过 `route.path` 判断 `isTeacherPage`。
- **流程**：前端 `chatJSON({ role: 'teacher', ... })` → 后端 `POST /chat` 创建会话（`scope=teacher`），返回 `chatId` 与 `stream: /ws/chat?chatId=xxx`；前端建立 WebSocket，发送 `chatId`，后端从 `get_messages(chatId)` 取历史，组装 prompt，调用 `invoke_llm`（可带资料上下文），流式通过 WS 推 `{ type: "answer", answer: chunk }`。
- **技术**：FastAPI WebSocket、`utils/websocket` 管理连接、`utils/llm` LangChain 流式、可选 `VectorStore`/资料拼接 context；前端 `Composer` 发问，`MarkdownView` 渲染回复。

### 3.2 文件库

- **路由**：`/teacher/file-library`。
- **实现**：`GET /files?role=teacher` 列表；`POST /files` 多文件上传，存 `storage/uploads/`，元数据写 JSON；`DELETE /files/{id}`。前端可勾选“教学文件夹”，对应 key `edumind-learning-folder-teacher`，供教案/测验/对话等“关联资料”使用。
- **技术**：FastAPI `UploadFile`、`aiofiles` 写文件、`config.storage_dir`。

### 3.3 教案

- **路由**：`/lesson-plan`。
- **实现**：前端提交课题 + 可选 materialIds → `POST /lesson-plan`；后端用 `_build_material_context_async` 从上传文件 sidecar 文本拼成上下文，调用 `LessonPlanAgent.execute()`，得到结构化 JSON（三维目标、重难点、教学过程、作业）；存 JSON 存储，返回 lesson_plan_id；`GET /lesson-plans/{id}/pdf` 用 reportlab 生成 PDF。
- **技术**：`LessonPlanAgent` 单次 LLM 调用、Pydantic 解析；reportlab 绘制 PDF。

### 3.4 教学幻灯片

- **路由**：`/slides`。
- **实现**：`POST /slides/generate` 传 topic、page_count、可选 materials；`SlidesAgent` 先用 DeepSeek 生成大纲 JSON（每页 title + bullets），再按页调用即梦生成**无字配图**，图片存 `storage/slides/`；返回 slide_id 与每页的 title、bullets、imageUrl。前端展示大纲+图；下载为 zip 或单图。
- **技术**：DeepSeek 大纲 + 即梦图像 API；无 pptx 生成避免字体/排版问题。

### 3.5 教学视频

- **路由**：`/teaching-video`。
- **实现**：`POST /teaching-video` 创建任务；前端连 `WS /ws/teaching-video`；后端 `TeachingVideoAgent` 生成讲解脚本 → 即梦文生视频（火山方舟 3.0 1080P）→ 脚本用 Edge TTS 配音 → ffmpeg 合成音视频为 MP4，存 `storage/teaching_videos/`；WS 推送进度与最终视频 URL。
- **技术**：即梦文生视频 API、`utils/tts` Edge TTS、`utils/teaching_video_audio` 合成、WebSocket 流式状态。

### 3.6 bilibili视频备课（教师端）

- **路由**：`/teacher/bili-learning`。
- **实现**：教师输入课题关键词，前端调用 `GET /api/bilibili/search`；后端 FastAPI `bilibili.py` 转发到 Node Bridge，Bridge 通过 MCP Tool 检索 B站并返回结构化结果（标题、封面、BV号、UP主、时长、简介）；点击卡片跳转对应视频用于备课。
- **技术**：`@modelcontextprotocol/sdk` + `StdioClientTransport`、Node Bridge + FastAPI 转发、前端结果卡片流与 `referrerpolicy="no-referrer"` 封面加载。

### 3.7 测验（教师端）

- **路由**：`/teacher/quiz`。
- **实现**：教师端侧重“出题”：`POST /quiz` 创建，`WS /ws/quiz` 流式收题；题目存 JSON；教师可查看题目与统计，不参与作答。与学生端共用 `Quiz.vue`，通过 `isTeacherPage` 隐藏作答 UI、只展示题目列表/历史。

### 3.8 试卷

- **路由**：`/teacher/paper`。
- **实现**：`POST /paper` + `WS /ws/paper` 流式生成选择/填空/应用题；存 JSON；`GET /papers/{id}/pdf` 用 reportlab 生成试卷 PDF。
- **技术**：`PaperAgent` 流式生成、后端组装完整 paper 后 reportlab 排版。

### 3.9 教学记录汇

- **路由**：`/teaching-records`。
- **实现**：前端聚合调用：对话列表、教案列表、幻灯片、教学视频、测验、试卷；展示历史卡片、主题词云、趋势图（如 ECharts）；左侧概览、右侧详情。
- **技术**：多接口并行请求、前端状态汇总；可选图表库。

---

## 四、学生端功能实现细节

### 4.1 对话（学生控制台）

- **路由**：`/chat`。
- **实现**：与教师端同一套后端，`role=student`；`scope=student` 的会话独立存储；前端 `chatJSON({ role: 'student', ... })`；学习资料文件夹 key 为 `edumind-learning-folder`；欢迎区标题“学生控制台”。
- **技术**：与 3.1 相同，仅 role/scope 与前端文案不同。

### 4.2 文件库（学生）

- **路由**：`/file-library`。
- **实现**：`GET/POST/DELETE /files?role=student`；学生端“学习文件夹”key 为 `edumind-learning-folder`，供对话、笔记、测验等挂载。
- **技术**：与教师文件库同一 `FileLibrary.vue`，`isTeacherPage` 为 false。

### 4.3 智能笔记

- **路由**：`/smart-notes`。
- **实现**：`POST /smartnotes` 返回 noteId 与 stream URL；`WS /ws/smartnotes` 流式生成康奈尔笔记；可选 materialIds 拼上下文；结果存 JSON，PDF 导出由后端或前端调导出接口生成。
- **技术**：`NoteAgent`、流式 WS、parser 抽资料文本。

### 4.4 测验（学生端）

- **路由**：`/quiz`。
- **实现**：学生可“做测验”：创建或选择已有测验，WS 收题后前端展示题目；学生选答案后 `POST /quizzes/{id}/attempts/answer` 提交，后端判对错并写入 attempts；错题写入错题本（wrongbook）供错题本页使用。
- **技术**：quiz_agent 出题、attempts 存 JSON、错题与错题本接口联动。

### 4.5 播客

- **路由**：`/podcast`。
- **实现**：`POST /podcast` 创建；`WS /ws/podcast`：PodcastAgent 流式生成对话式脚本，按段通过 `text_to_speech` 合成音频，多段用 ffmpeg 拼接；前端可下载 MP3。
- **技术**：`utils/tts`、ffmpeg、WebSocket 进度与完成事件。

### 4.6 知识卡片

- **路由**：`/knowledge-cards`。
- **实现**：`POST /flashcards/decks` 传主题或 materialIds，`KnowledgeCardsAgent` 生成概念卡（概念+问答+填空）；存为 deck；前端列表与翻卡复习。
- **技术**：flashcards_agent、JSON 存储 deck/cards。

### 4.7 错题本

- **路由**：`/wrong-book`、`/wrong-book/practice`。
- **实现**：`GET /wrongbook/summary` 汇总错题数、掌握率、薄弱知识点、趋势；`POST /wrongbook/report` 用 WrongBookReportAgent 生成文字报告与建议；`POST /wrongbook/weak-points` 薄弱点与推荐题；错题来源为测验 attempts 中答错的题。
- **技术**：quiz attempts 数据、WrongBookReportAgent、KnowledgePointAgent 等。

### 4.8 学习记录汇

- **路由**：`/learning-records`。
- **实现**：前端聚合对话、智能笔记、播客、测验、知识卡片等历史；展示词云与学习趋势；与教学记录汇对称。
- **技术**：多 API 聚合、前端展示。

### 4.9 英语口语

- **路由**：`/english-speaking`。
- **实现**：`POST /speaking/generate` 生成题目与参考文本；学生录音上传 `POST /speaking/upload`；`POST /speaking/evaluate` 调讯飞 ISE 评测，返回分数与反馈；历史存 JSON。
- **技术**：讯飞 ISE API、TTS 生成示范音、ffmpeg 转 PCM 等。

### 4.10 B站视频学习（学生端）

- **路由**：`/bili-learning`。
- **实现**：学生输入学习关键词，调用同一 `GET /api/bilibili/search` 接口；页面展示视频卡片并支持一键跳转；搜索前展示 MCP 特点与功能特色，搜索后切换结果视图。
- **技术**：复用 MCP Bridge 检索链路，前端 Composition API 状态管理与响应式布局。

---

## 五、技术栈与面试可答点

- **前端**：Vue 3 Composition API + `<script setup>`、Pinia、Vue Router、TypeScript、TailwindCSS、Vite；双角色（教师/学生）通过 store + 路由区分，入口按钮先 setRole 再跳转避免进错端。
- **后端**：FastAPI 异步、Pydantic、aiofiles；WebSocket 用于对话/测验/教案/试卷/播客/笔记/教学视频等流式输出；统一错误与 CORS。
- **MCP 扩展**：新增 Node MCP Bridge（`@modelcontextprotocol/sdk`），以 stdio 连接 bilibili-mcp-js，实现 B站视频搜索能力并通过 FastAPI 对外统一 API。
- **LLM**：LangChain 封装多厂商（Gemini/OpenAI/Claude/DeepSeek/Ollama/OpenRouter/Grok），便于切换；Agent 层做 Prompt 工程与 JSON 解析。
- **存储**：JSON 文件存储为主，向量检索用嵌入+本地 JSON 或 FAISS；对话/测验等按 role 或 namespace 隔离。
- **文档与音视频**：PyMuPDF/mammoth/python-docx 解析；reportlab 生成 PDF；Edge TTS + ffmpeg 合成音频；即梦配图与文生视频。
- **部署**：前后端分离；`VITE_BACKEND_URL` 指向后端；可 Docker 化。

---

## 六、常见面试追问与简答

1. **对话为什么用 WebSocket 而不是 HTTP 流？**  
   需要服务端主动推送多段 chunk，且同一会话可能有多端；WebSocket 一次连接、双向通信，便于流式输出与进度推送。

2. **教师端和学生端数据如何隔离？**  
   通过 `role`/`scope` 区分：对话用 `scope=teacher|student` 存不同 namespace；文件库、测验、attempts 等接口都带 `role` 参数，存储 key 或表带 role 前缀。

3. **教案/试卷 PDF 如何生成？**  
   后端用 Python `reportlab` 根据结构化数据（标题、段落、列表）绘制 PDF，通过 `FileResponse` 或 GET 导出接口返回。

4. **幻灯片为什么不直接生成 pptx？**  
   避免字体与中文排版问题；采用“大纲 JSON + 即梦配图”方案，前端展示大纲+图，需要时再考虑服务端 python-pptx 生成。

5. **教学视频链路？**  
   主题+资料 → LLM 脚本 → 即梦文生视频（火山方舟）→ Edge TTS 配音 → ffmpeg 合成为 MP4，WebSocket 推送各阶段状态。

6. **错题本数据从哪来？**  
   来自测验的 attempts：学生提交答案后后端判对错，错题写入错题库；错题本页调用 wrongbook 相关接口做汇总、报告与薄弱点分析。

7. **首页点“学生端入口”却进教师对话？**  
   已修复：入口改为按钮 + 点击先 `roleStore.setRole('student')` 再 `router.push('/chat')`，保证角色与路由一致。

8. **文件库后切页面空白？**  
   已修复：App.vue 中为 RouterView 外包一层带 `min-h-full` 的 keyed div，并给父容器 `min-h-0 flex flex-col`，保证过渡时新页面有高度、正常渲染。

---

以上内容覆盖项目结构、教师端/学生端各功能实现方式、主要技术选型与面试可答细节，可直接用于面试前的项目梳理与“细节拷打”准备。
