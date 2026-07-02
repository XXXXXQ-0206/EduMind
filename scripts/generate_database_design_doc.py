from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Iterable

import win32com.client as win32


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "数据库设计说明书模板.doc"
OUTPUT_DIR = ROOT / "docs" / "generated"
OUTPUT_DOC = OUTPUT_DIR / "EduMind数据库设计说明书.doc"
OUTPUT_DOCX = OUTPUT_DIR / "EduMind数据库设计说明书.docx"
OUTPUT_PDF = OUTPUT_DIR / "EduMind数据库设计说明书.pdf"
ANALYSIS_JSON = OUTPUT_DIR / "database_design_template_analysis.json"
VALIDATION_JSON = OUTPUT_DIR / "database_design_validation.json"

COMPANY = "重庆大学"
SYSTEM_NAME = "EduMind 智能教育微服务系统"
DOC_NAME = "EduMind数据库设计说明书"
DOC_NO = "EDUMIND-DBD-2026-0701"
AUTHOR = "熊骞 邱道玉"
REVIEWER = "陈奕博 叶博豪"
DOC_DATE = "2026年7月1日"

WD_FIND_CONTINUE = 1
WD_REPLACE_ALL = 2
WD_GO_TO_PAGE = 1
WD_GO_TO_ABSOLUTE = 1
WD_FORMAT_DOCUMENT = 0
WD_FORMAT_XML_DOCUMENT = 16
WD_FORMAT_PDF = 17
WD_AUTO_FIT_WINDOW = 2
WD_ALIGN_LEFT = 0
WD_ALIGN_CENTER = 1
WD_ALIGN_RIGHT = 2
WD_COLLAPSE_END = 0
WD_STYLE_NORMAL = -1
WD_STYLE_HEADING_1 = -2
WD_STYLE_HEADING_2 = -3
WD_STYLE_HEADING_3 = -4
WD_OUTLINE_LEVEL_BODY_TEXT = 10


DIRECTORY_ANALYSIS = [
    ["目录/文件", "职责", "与数据库设计的关系"],
    ["backend/api/routes", "对外业务 API，包含认证、文件、聊天、测验、笔记、试卷、课件、教学视频等入口。", "各业务路由通过 JSONStorage、RAG、ObjectStore 写入 PostgreSQL JSONB、pgvector 或对象存储。"],
    ["backend/core", "应用装配、服务注册、网关、Celery 任务分发和生命周期管理。", "明确微服务边界，统一连接共享 PostgreSQL、Redis、MinIO 等基础设施。"],
    ["backend/infrastructure", "KV、对象存储、事件总线、任务租约、任务队列适配器。", "定义数据库访问抽象，PostgreSQL JSONB 为默认 KV 运行时。"],
    ["backend/utils", "认证、业务存储、LLM、解析、实时事件、上传对象辅助等公共模块。", "包含认证表、KV 表、向量表的实际建表逻辑。"],
    ["backend/rag", "文档加载、文本分段、索引、检索和 agent 材料上下文编排。", "维护 rag:file 元数据和 file:{file_id} 向量命名空间。"],
    ["frontend/src", "Vue 前端页面和 API 封装。", "文件库、学习资料夹和生成任务页面向后端传递 materialIds 与索引状态。"],
    ["deploy/docker 与 docker-compose.yml", "容器镜像、微服务、PostgreSQL、Redis、MinIO 编排。", "给出数据库版本、连接地址、默认账户和运行拓扑。"],
    ["docs、tests、scripts", "架构说明、测试用例、迁移和启动脚本。", "提供设计依据、验证方案和数据库迁移维护工具。"],
]

DEFINITIONS = [
    ["术语", "说明"],
    ["PostgreSQL", "系统主数据库，保存认证、会话、JSONB 状态和 pgvector 向量数据。"],
    ["JSONB KV", "用 edumind_kv 表承载业务对象的键值结构，保持旧 JSONStorage API 的兼容性。"],
    ["pgvector", "PostgreSQL 向量扩展，保存文档分段 embedding 并支持相似度检索。"],
    ["ObjectStore", "对象文件存储抽象，生产环境采用 MinIO/S3，本地开发可使用 storage 目录。"],
    ["RAG", "检索增强生成流程，agent 调用前根据查询从多文件向量库取回相关片段。"],
    ["Celery/Redis", "长任务队列、事件通道、任务租约和 SSE/WebSocket 进度通知的运行基础。"],
]

SERVICE_FLOW = [
    ["服务/模块", "读写数据", "数据交互方式"],
    ["identity", "用户、会话、认证相关聊天索引", "直接读写 PostgreSQL 认证表，并提供 token 解析接口。"],
    ["asset-library", "上传文件 metadata、rag:file 状态、file_meta 索引快照、对象文件", "文件写入 ObjectStore，元数据写入 edumind_kv，索引任务写入 pgvector。"],
    ["learning-content", "聊天、测验、笔记、知识卡片、错题与规划任务", "业务状态以 KV 键保存，生成前调用 RAG 取多文件上下文。"],
    ["teaching-content", "教案、试卷、课件、教学视频", "写入业务 KV 和导出对象，使用教师端文件库 RAG 上下文。"],
    ["media-generation", "播客、语音评测、Bilibili 搜索结果", "长任务经 Celery/Redis 调度，结果元数据写入 KV，对象写入 ObjectStore。"],
    ["ai-core", "LLM 与 embedding 调用", "为 RAG 索引和生成服务提供模型访问能力，不直接保存业务主体数据。"],
    ["generation-worker", "异步生成任务、文件索引任务", "从 Redis/Celery 队列取任务，访问 PostgreSQL、pgvector 和 ObjectStore 完成落库。"],
]

DATABASE_CONNECTIONS = [
    ["项目", "配置"],
    ["数据库类型", "PostgreSQL + pgvector"],
    ["数据库版本", "PostgreSQL 16，Docker 镜像 pgvector/pgvector:pg16"],
    ["数据库名称", "edumind"],
    ["容器内地址", "postgres:5432"],
    ["DSN", "postgresql://edumind:edumind@postgres:5432/edumind"],
    ["用户名", "edumind"],
    ["密码", "开发与本地容器默认值为 edumind；生产环境由 POSTGRES_PASSWORD/POSTGRES_DSN 注入并由部署环境管理。"],
    ["向量表", "edumind_vectors"],
    ["对象存储", "MinIO/S3 bucket: edumind，内部地址 http://minio:9000"],
    ["Redis", "redis://redis:6379/0"],
]

TABLES = [
    {
        "heading": "3.1 用户信息表[edumind_auth_users]",
        "caption": "用户信息表[edumind_auth_users]",
        "intro": "该表由 identity 服务维护，保存系统登录主体。密码不保存明文，采用 PBKDF2 哈希和独立 salt。",
        "rows": [
            ["id", "integer identity", "是", "是", "用户唯一编号，作为认证域主键。"],
            ["username", "text", "否", "是", "登录用户名，设置唯一约束。"],
            ["password_hash", "text", "否", "是", "PBKDF2 计算后的密码哈希值。"],
            ["password_salt", "text", "否", "是", "密码哈希盐值，按用户独立生成。"],
            ["created_at", "timestamptz", "否", "是", "用户创建时间。"],
            ["updated_at", "timestamptz", "否", "是", "用户资料或密码更新时间。"],
        ],
    },
    {
        "heading": "3.2 会话令牌表[edumind_auth_sessions]",
        "caption": "会话令牌表[edumind_auth_sessions]",
        "intro": "该表保存登录态 token。用户退出、改密或注销时同步删除会话记录。",
        "rows": [
            ["token", "text", "是", "是", "登录会话令牌，使用 secrets.token_urlsafe 生成。"],
            ["user_id", "integer", "否", "是", "所属用户，外键关联 edumind_auth_users(id)，级联删除。"],
            ["created_at", "timestamptz", "否", "是", "会话创建时间。"],
            ["expires_at", "timestamptz", "否", "是", "会话过期时间，当前有效期为 14 天。"],
        ],
    },
    {
        "heading": "3.3 聊天会话表[edumind_auth_chats]",
        "caption": "聊天会话表[edumind_auth_chats]",
        "intro": "该表保存教师端和学生端的聊天会话索引，具体消息进入消息表，业务生成产物进入 KV。",
        "rows": [
            ["id", "text", "是", "是", "聊天会话 ID，采用 UUID 字符串。"],
            ["user_id", "integer", "否", "是", "所属用户，外键关联用户表。"],
            ["title", "text", "否", "是", "会话标题，取用户问题或主题前 100 字。"],
            ["scope", "text", "否", "是", "student 或 teacher，用于区分学生端和教师端。"],
            ["response_length", "text", "否", "是", "回复长度配置，默认 Short。"],
            ["include_materials", "boolean", "否", "是", "是否启用文件库材料上下文。"],
            ["material_ids", "jsonb", "否", "是", "学习资料夹或备课资料夹选中的文件 ID 列表。"],
            ["created_at", "timestamptz", "否", "是", "创建时间。"],
            ["updated_at", "timestamptz", "否", "是", "最近消息或设置更新时间。"],
        ],
    },
    {
        "heading": "3.4 聊天消息表[edumind_auth_chat_messages]",
        "caption": "聊天消息表[edumind_auth_chat_messages]",
        "intro": "该表保存聊天消息流水，按 chat_id 和自增 id 排序读取。",
        "rows": [
            ["id", "integer identity", "是", "是", "消息流水主键。"],
            ["chat_id", "text", "否", "是", "所属聊天会话，外键关联 edumind_auth_chats(id)。"],
            ["role", "text", "否", "是", "消息角色，取 user 或 assistant。"],
            ["content", "text", "否", "是", "消息正文。"],
            ["at", "bigint", "否", "是", "客户端展示用毫秒时间戳。"],
        ],
    },
    {
        "heading": "3.5 业务键值状态表[edumind_kv]",
        "caption": "业务键值状态表[edumind_kv]",
        "intro": "该表是微服务共享状态的主承载表，使用 key 前缀划分业务对象，value 保存 JSONB 文档。",
        "rows": [
            ["key", "text", "是", "是", "业务键，包含对象类型、对象 ID 和子资源名称。"],
            ["value", "jsonb", "否", "是", "业务状态 JSON，包括生成结果、材料配置、索引状态等。"],
            ["updated_at", "timestamptz", "否", "是", "写入或更新时自动刷新。"],
        ],
    },
    {
        "heading": "3.6 向量分段表[edumind_vectors]",
        "caption": "向量分段表[edumind_vectors]",
        "intro": "该表由 pgvector 管理多文件 RAG 文档分段。每个上传文件使用独立 namespace，便于删除和重建。",
        "rows": [
            ["id", "bigserial", "是", "是", "向量记录主键。"],
            ["namespace", "text", "否", "是", "向量命名空间。文件库使用 file:{file_id}。"],
            ["ordinal", "integer", "否", "是", "分段在当前 namespace 内的顺序号。"],
            ["text", "text", "否", "是", "文档分段原文，用于返回给 agent 作为材料上下文。"],
            ["metadata", "jsonb", "否", "是", "文件 ID、文件名、对象 key、chunk_index、char_start、char_end、content_hash 等。"],
            ["embedding", "vector", "否", "是", "文本向量，由 embedding provider 生成。"],
            ["created_at", "timestamptz", "否", "是", "向量写入时间。"],
        ],
    },
    {
        "heading": "3.7 RAG文件索引元数据[rag:file:{file_id}]",
        "caption": "RAG文件索引元数据[rag:file:{file_id}]",
        "intro": "该对象存储在 edumind_kv 中，用于记录文件是否完成解析、分段、向量化和索引。",
        "rows": [
            ["fileId", "string", "是", "是", "文件库 ID，与上传 metadata 的 id 一致。"],
            ["status", "string", "否", "是", "pending、indexing、indexed、failed 或 unsupported。"],
            ["owner_id", "integer", "否", "是", "文件所属用户。"],
            ["owner_username", "string", "否", "是", "文件所属用户名。"],
            ["role", "string", "否", "是", "student 或 teacher。"],
            ["objectKey", "string", "否", "是", "对象存储 key，例如 uploads/...。"],
            ["originalName", "string", "否", "是", "用户上传时的原始文件名。"],
            ["mimeType", "string", "否", "是", "文件 MIME 类型。"],
            ["size", "integer", "否", "是", "文件字节数。"],
            ["contentHash", "string", "否", "否", "SHA-256 内容 hash，用于判断是否需要重建索引。"],
            ["chunkCount", "integer", "否", "是", "索引成功后的分段数量。"],
            ["indexedAt", "string", "否", "否", "完成索引的 ISO 时间。"],
            ["error", "string", "否", "否", "索引失败或不支持时的错误说明。"],
        ],
    },
]

KV_PREFIXES = [
    ["键前缀", "值类型", "用途"],
    ["files:user:{user_id}", "jsonb array", "学生端文件库 metadata 列表。"],
    ["files_teacher:user:{user_id}", "jsonb array", "教师端备课文件库 metadata 列表。"],
    ["file_meta:{file_id}", "jsonb object", "文件索引任务读取的文件 metadata 快照。"],
    ["rag:file:{file_id}", "jsonb object", "文件 RAG 索引状态与分段统计。"],
    ["chat:{chat_id}", "jsonb object", "兼容层聊天元数据。"],
    ["chat:{chat_id}:messages", "jsonb array", "兼容层聊天消息列表。"],
    ["quiz:{quiz_id}", "jsonb object", "测验任务元数据和生成状态。"],
    ["quiz:{quiz_id}:quiz", "jsonb array", "测验题目和答案解析。"],
    ["note:{note_id}", "jsonb object", "智能笔记元数据和导出文件信息。"],
    ["note:{note_id}:notes", "jsonb object", "结构化笔记正文。"],
    ["podcast:{pid}", "jsonb object", "播客元数据、音频地址和状态。"],
    ["podcast:{pid}:script", "jsonb object", "播客脚本。"],
    ["lesson_plan:{id}", "jsonb object", "教案任务元数据。"],
    ["lesson_plan:{id}:plan", "jsonb object", "教案结构化结果。"],
    ["paper:{id}", "jsonb object", "试卷任务元数据。"],
    ["paper:{id}:paper", "jsonb array", "试卷题目列表。"],
    ["slide:{id}", "jsonb object", "课件元数据和下载对象 key。"],
    ["slide:{id}:slides", "jsonb array", "课件页面结构。"],
    ["video:{id}", "jsonb object", "教学视频元数据。"],
    ["video:{id}:script", "jsonb object", "教学视频脚本。"],
    ["flashcard_deck:{id}", "jsonb object", "知识卡片卡组详情。"],
    ["planner:tasks:user:{user_id}", "jsonb array", "学习规划任务列表。"],
]

INDEXES = [
    ["对象", "索引/约束", "说明"],
    ["edumind_auth_users", "PRIMARY KEY(id), UNIQUE(username)", "支持登录名唯一性和用户主键查询。"],
    ["edumind_auth_sessions", "PRIMARY KEY(token), FK(user_id)", "按 token 查会话，用户删除时级联清理。"],
    ["edumind_auth_chats", "PRIMARY KEY(id), INDEX(user_id, updated_at DESC)", "按用户和更新时间列出会话。"],
    ["edumind_auth_chat_messages", "PRIMARY KEY(id), INDEX(chat_id, id)", "按会话顺序读取消息。"],
    ["edumind_kv", "PRIMARY KEY(key)", "按业务键读写 JSONB 状态；list_prefix 使用 key 前缀扫描。"],
    ["edumind_vectors", "PRIMARY KEY(id), INDEX(namespace, ordinal)", "按文件 namespace 删除、重建和检索分段。"],
]

DATA_DICTIONARY = [
    ["字段/枚举", "取值或格式", "说明"],
    ["scope / role", "student, teacher", "区分学生端学习资料和教师端备课资料。"],
    ["generation status", "pending, generating, ready, error", "生成类任务统一状态。"],
    ["RAG status", "pending, indexing, indexed, failed, unsupported", "文件索引状态。"],
    ["objectKey", "uploads/{timestamp}-{uuid}-{filename}", "上传对象在 MinIO/S3 或本地 ObjectStore 中的路径。"],
    ["vector namespace", "file:{file_id}", "每个文件独立向量命名空间。"],
    ["materialIds", "jsonb array[string]", "agent 调用前选中的多文件 ID 列表。"],
    ["contentHash", "sha256 hex", "用于识别文件内容是否变化。"],
]

SECURITY_ITEMS = [
    ["措施", "设计说明"],
    ["身份认证", "identity 服务统一维护用户和会话，业务服务在远程模式下通过内部接口解析 Bearer token。"],
    ["密码保护", "密码使用 PBKDF2-HMAC-SHA256 与独立 salt 保存，不落明文。"],
    ["数据隔离", "文件、任务、生成记录均带 owner_id/owner_username，读取和删除前校验所属用户。"],
    ["密钥管理", ".env、数据库密码、S3 密钥、模型 API Key 不进入 Git，由部署环境注入。"],
    ["对象安全", "ObjectStore 使用规范化 object key，删除前检查根路径，避免越权路径访问。"],
    ["RAG边界", "检索只在用户选中的 materialIds 范围内执行，跨文件检索仍保留用户和角色元数据。"],
    ["任务可靠性", "Celery/Redis 配置可见性超时、重试次数和任务租约，避免长任务重复写入。"],
]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def start_word():
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    return word


def close_word(word) -> None:
    try:
        word.Quit()
    finally:
        try:
            import pythoncom

            pythoncom.CoUninitialize()
        except Exception:
            pass


def clean_text(value: str) -> str:
    return str(value or "").replace("\r", "\n").replace("\x07", "").strip()


def analyze_template(word) -> dict[str, Any]:
    doc = word.Documents.Open(str(TEMPLATE), False, True)
    try:
        tables: list[dict[str, Any]] = []
        for index in range(1, doc.Tables.Count + 1):
            table = doc.Tables(index)
            rows: list[list[str]] = []
            for row in range(1, min(table.Rows.Count, 20) + 1):
                row_values: list[str] = []
                for col in range(1, table.Columns.Count + 1):
                    try:
                        row_values.append(clean_text(table.Cell(row, col).Range.Text))
                    except Exception:
                        row_values.append("<merged>")
                rows.append(row_values)
            tables.append(
                {
                    "index": index,
                    "rows": table.Rows.Count,
                    "columns": table.Columns.Count,
                    "sample": rows,
                }
            )

        shapes: list[dict[str, Any]] = []
        for index in range(1, doc.Shapes.Count + 1):
            shape = doc.Shapes(index)
            item: dict[str, Any] = {
                "index": index,
                "type": int(shape.Type),
                "name": str(shape.Name),
                "width": float(shape.Width),
                "height": float(shape.Height),
            }
            try:
                if shape.TextFrame.HasText:
                    item["text"] = clean_text(shape.TextFrame.TextRange.Text)
            except Exception:
                item["text"] = ""
            shapes.append(item)

        analysis = {
            "template": str(TEMPLATE),
            "paragraphs": doc.Paragraphs.Count,
            "tables": tables,
            "inlineShapes": doc.InlineShapes.Count,
            "shapes": shapes,
            "sections": doc.Sections.Count,
            "pages": doc.ComputeStatistics(2),
            "fullText": clean_text(doc.Content.Text),
        }
        ANALYSIS_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
        return analysis
    finally:
        doc.Close(False)


def replace_in_range(rng, find_text: str, replace_text: str) -> None:
    find = rng.Find
    find.ClearFormatting()
    find.Replacement.ClearFormatting()
    find.Execute(
        FindText=find_text,
        MatchCase=False,
        MatchWholeWord=False,
        MatchWildcards=False,
        MatchSoundsLike=False,
        MatchAllWordForms=False,
        Forward=True,
        Wrap=WD_FIND_CONTINUE,
        Format=False,
        ReplaceWith=replace_text,
        Replace=WD_REPLACE_ALL,
    )


def replace_all(doc, find_text: str, replace_text: str) -> None:
    replace_in_range(doc.Content, find_text, replace_text)
    for index in range(1, doc.Shapes.Count + 1):
        shape = doc.Shapes(index)
        try:
            if shape.TextFrame.HasText:
                replace_in_range(shape.TextFrame.TextRange, find_text, replace_text)
        except Exception:
            continue


def prepare_copy() -> None:
    ensure_output_dir()
    for path in (OUTPUT_DOC, OUTPUT_DOCX, OUTPUT_PDF):
        if path.exists():
            path.unlink()
    shutil.copy2(TEMPLATE, OUTPUT_DOC)


def style_by_names(doc, names: Iterable[Any]):
    for name in names:
        try:
            return doc.Styles(name)
        except Exception:
            continue
    return doc.Styles(WD_STYLE_NORMAL)


def set_font(selection, font: str, size: float, bold: bool = False) -> None:
    selection.Font.NameFarEast = font
    selection.Font.Name = "Times New Roman"
    selection.Font.Size = size
    selection.Font.Bold = -1 if bold else 0


def add_paragraph(
    selection,
    doc,
    text: str = "",
    *,
    style: Any = None,
    font: str = "宋体",
    size: float = 12,
    bold: bool = False,
    align: int = WD_ALIGN_LEFT,
    first_indent: bool = True,
    before: float = 0,
    after: float = 6,
) -> None:
    if style is not None:
        selection.Style = style
    else:
        selection.Style = doc.Styles(WD_STYLE_NORMAL)
    set_font(selection, font, size, bold)
    selection.ParagraphFormat.Alignment = align
    selection.ParagraphFormat.FirstLineIndent = 24 if first_indent else 0
    selection.ParagraphFormat.SpaceBefore = before
    selection.ParagraphFormat.SpaceAfter = after
    selection.ParagraphFormat.LineSpacingRule = 1
    selection.ParagraphFormat.LineSpacing = 18
    if text:
        selection.TypeText(text)
    selection.TypeParagraph()


def add_heading(selection, doc, text: str, level: int) -> None:
    if level == 1:
        style = style_by_names(doc, ["标题 1", "Heading 1", WD_STYLE_HEADING_1])
        add_paragraph(selection, doc, text, style=style, font="黑体", size=18, bold=True, first_indent=False, before=12, after=12)
    elif level == 2:
        style = style_by_names(doc, ["标题 2", "Heading 2", WD_STYLE_HEADING_2])
        add_paragraph(selection, doc, text, style=style, font="黑体", size=14, bold=True, first_indent=False, before=10, after=8)
    else:
        style = style_by_names(doc, ["标题 3", "Heading 3", WD_STYLE_HEADING_3])
        add_paragraph(selection, doc, text, style=style, font="黑体", size=12, bold=True, first_indent=False, before=8, after=6)


def add_table(selection, doc, rows: list[list[str]], *, caption: str | None = None, font_size: float = 9) -> None:
    if caption:
        add_paragraph(selection, doc, caption, font="宋体", size=11, bold=True, first_indent=False, after=3)
    if not rows:
        return
    row_count = len(rows)
    col_count = max(len(row) for row in rows)
    table = doc.Tables.Add(selection.Range, row_count, col_count)
    table.Borders.Enable = 1
    table.AllowAutoFit = True
    for row_index, row in enumerate(rows, start=1):
        for col_index in range(1, col_count + 1):
            text = row[col_index - 1] if col_index <= len(row) else ""
            cell_range = table.Cell(row_index, col_index).Range
            cell_range.Text = str(text)
            cell_range.Font.NameFarEast = "宋体"
            cell_range.Font.Name = "Times New Roman"
            cell_range.Font.Size = font_size
            if row_index == 1:
                cell_range.Font.Bold = -1
                table.Cell(row_index, col_index).Shading.BackgroundPatternColor = 14277081
    try:
        table.Rows(1).HeadingFormat = True
    except Exception:
        pass
    table.AutoFitBehavior(WD_AUTO_FIT_WINDOW)
    selection.SetRange(table.Range.End, table.Range.End)
    selection.TypeParagraph()


def add_table_5(selection, doc, rows: list[list[str]]) -> None:
    add_table(selection, doc, [["字段名", "数据类型及长度", "主键", "非空", "描述"], *rows], font_size=8.5)


def add_numbered_lines(selection, doc, lines: list[str]) -> None:
    for line in lines:
        add_paragraph(selection, doc, line, size=12, first_indent=True, after=3)


def insert_body(word, doc) -> None:
    start_range = doc.GoTo(What=WD_GO_TO_PAGE, Which=WD_GO_TO_ABSOLUTE, Count=3)
    start = start_range.Start
    end = doc.Content.End - 1
    if end > start:
        doc.Range(Start=start, End=end).Delete()
    selection = word.Selection
    selection.SetRange(start, start)

    add_paragraph(selection, doc, DOC_NAME, font="黑体", size=18, bold=True, align=WD_ALIGN_CENTER, first_indent=False, after=18)

    add_heading(selection, doc, "1 引言", 1)
    add_heading(selection, doc, "1.1 编写目的", 2)
    add_paragraph(
        selection,
        doc,
        "本文档记录 EduMind 智能教育微服务系统的数据库设计。编写前对项目目录、后端服务边界、数据访问适配器、前端材料选择流程、Docker 运行环境和 RAG 文件库链路进行了梳理，确认系统以 PostgreSQL、pgvector、Redis 和 MinIO/S3 作为共享数据基础设施。",
    )
    add_paragraph(
        selection,
        doc,
        "文档用于说明数据库对象、字段含义、键值状态、向量索引、数据交互方式、安全控制和运维约定，为后续开发、测试、部署和维护提供一致依据。",
    )
    add_paragraph(selection, doc, "阅读对象为：", first_indent=False)
    add_numbered_lines(
        selection,
        doc,
        [
            "1）负责系统架构、质量管理和项目验收的管理人员；",
            "2）负责后端微服务、文件库、RAG 和任务队列的开发人员；",
            "3）负责前端页面、联调、测试设计和数据验证的工程人员；",
            "4）负责部署、备份恢复、安全配置和运行维护的人员。",
        ],
    )
    add_table(selection, doc, DIRECTORY_ANALYSIS, caption="表1-1 项目前期目录与数据职责分析", font_size=8.5)

    add_heading(selection, doc, "1.2 背景", 2)
    add_paragraph(selection, doc, "开发软件名称：EduMind 智能教育微服务系统", first_indent=False)
    add_paragraph(selection, doc, "项目任务提出者：重庆大学", first_indent=False)
    add_paragraph(selection, doc, "项目开发者：熊骞、邱道玉", first_indent=False)
    add_paragraph(selection, doc, "用户：教师、学生、系统管理员和运行维护人员", first_indent=False)
    add_paragraph(selection, doc, "实现软件单位：重庆大学", first_indent=False)
    add_paragraph(
        selection,
        doc,
        "系统提供学习资料问答、测验、智能笔记、知识卡片、教案、试卷、课件、教学视频、播客和学习规划等功能。后端按 identity、learning-content、asset-library、ai-core、media-generation、teaching-content 和 generation-worker 拆分运行，统一通过 API Gateway 对外服务。",
    )

    add_heading(selection, doc, "1.3 定义", 2)
    add_table(selection, doc, DEFINITIONS, caption="表1-2 术语定义", font_size=9)

    add_heading(selection, doc, "1.4 参考资料", 2)
    add_numbered_lines(
        selection,
        doc,
        [
            "1）README.md，项目结构、启动方式和基础设施说明；",
            "2）knowledge.md，微服务边界、部署和数据迁移说明；",
            "3）docs/architecture/backend-service-boundaries.md，后端服务边界说明；",
            "4）docs/superpowers/plans/2026-07-01-multi-file-rag-agent-context.md，多文件 RAG agent 上下文设计资料；",
            "5）backend/config.py、backend/infrastructure/kv_store.py、backend/utils/auth_db.py、backend/utils/storage.py，数据库和存储适配器实现；",
            "6）docker-compose.yml，PostgreSQL、Redis、MinIO 和各微服务运行配置。",
        ],
    )

    add_heading(selection, doc, "2 外部设计", 1)
    add_heading(selection, doc, "2.1 标识符和状态", 2)
    add_paragraph(selection, doc, "数据库软件的名称：PostgreSQL 16 + pgvector", first_indent=False)
    add_paragraph(selection, doc, "数据库的名称为：edumind", first_indent=False)
    add_paragraph(
        selection,
        doc,
        "数据库对象采用 public schema 下的显式表名。认证域使用 edumind_auth_ 前缀，业务键值状态使用 edumind_kv，向量索引使用 edumind_vectors。RAG 文件级逻辑对象通过 rag:file:{file_id} 键和 file:{file_id} 向量命名空间标识。",
    )

    add_heading(selection, doc, "2.2 使用它的程序", 2)
    add_paragraph(
        selection,
        doc,
        "本数据库用于 EduMind 智能教育微服务系统。API Gateway 负责统一入口，各业务服务通过共享适配器访问 PostgreSQL、pgvector、Redis 和 ObjectStore。长任务由 Celery/Redis 分发，生成结果和进度状态写入共享存储。",
    )
    add_table(selection, doc, SERVICE_FLOW, caption="表2-1 服务与数据交互关系", font_size=8.5)

    add_heading(selection, doc, "2.3 命名约定", 2)
    add_numbered_lines(
        selection,
        doc,
        [
            "1）物理表名统一使用小写英文和下划线，例如 edumind_auth_users、edumind_vectors。",
            "2）认证域表名前缀为 edumind_auth_，业务状态表为 edumind_kv，向量表为 edumind_vectors。",
            "3）KV 业务键采用 type:{id}:subtype 形式，例如 quiz:{quiz_id}:quiz、rag:file:{file_id}。",
            "4）文件对象路径采用 uploads/{timestamp}-{uuid}-{filename}，导出文件按业务目录归档。",
            "5）RAG 向量命名空间采用 file:{file_id}，便于针对单个文件删除、重建和检索。",
            "6）时间字段使用 timestamptz 或 ISO 字符串；前端展示用毫秒时间戳时字段命名为 at。",
        ],
    )

    add_heading(selection, doc, "2.4 设计约定", 2)
    add_paragraph(
        selection,
        doc,
        "系统采用“关系表 + JSONB KV + 向量表 + 对象存储”的组合设计。认证、会话和聊天消息采用关系表保证约束和查询效率；业务生成产物以 JSONB KV 保存，适配多种 AI 生成结构；文件原始内容进入 ObjectStore；文件文本分段进入 pgvector，以支持多文件 RAG 检索。",
    )
    add_paragraph(
        selection,
        doc,
        "数据库访问由适配器集中封装，业务路由不直接拼接本地 storage 路径。文件上传、解析、索引、检索和 agent 调用前上下文整合均通过 objectKey、RAG 状态和向量命名空间完成。",
    )

    add_heading(selection, doc, "2.5 数据库地址和用户名密码", 2)
    add_table(selection, doc, DATABASE_CONNECTIONS, caption="表2-2 数据库和基础设施连接配置", font_size=9)

    add_heading(selection, doc, "2.6 数据交互概览", 2)
    add_table(
        selection,
        doc,
        [
            ["步骤", "数据流向", "落库对象"],
            ["用户登录", "frontend -> api-gateway -> identity", "edumind_auth_users、edumind_auth_sessions"],
            ["上传文件", "frontend -> asset-library -> ObjectStore/KV", "files:user、files_teacher:user、file_meta、rag:file"],
            ["文件索引", "generation-worker -> parser/embedding -> pgvector", "edumind_vectors(namespace=file:{file_id})"],
            ["agent 生成", "业务服务 -> RAG context -> LLM -> KV/ObjectStore", "quiz/note/paper/slide/video 等 KV 键和导出对象"],
            ["进度通知", "worker -> Redis Pub/Sub/SSE/WebSocket -> frontend", "Redis 事件通道和任务队列"],
        ],
        caption="表2-3 主要数据流说明",
        font_size=8.5,
    )

    add_heading(selection, doc, "3 结构设计", 1)
    for table_def in TABLES:
        add_heading(selection, doc, table_def["heading"], 2)
        add_paragraph(selection, doc, table_def["intro"])
        add_paragraph(selection, doc, table_def["caption"], first_indent=False, after=3)
        add_table_5(selection, doc, table_def["rows"])

    add_heading(selection, doc, "3.8 主要业务键值对象[edumind_kv]", 2)
    add_paragraph(
        selection,
        doc,
        "业务生成结果和配置项以 key 前缀组织在 edumind_kv 中。该设计减少频繁建表带来的迁移成本，同时保留 PostgreSQL 的 JSONB 查询、备份和事务能力。",
    )
    add_table(selection, doc, KV_PREFIXES, caption="表3-8 主要 KV 键前缀", font_size=8)

    add_heading(selection, doc, "3.9 索引和约束设计", 2)
    add_table(selection, doc, INDEXES, caption="表3-9 索引和约束", font_size=8.5)

    add_heading(selection, doc, "3.10 对象存储键设计", 2)
    add_table(
        selection,
        doc,
        [
            ["对象目录", "内容", "数据库关联字段"],
            ["uploads/", "用户上传的 PDF、Office、文本等原始资料。", "files metadata.objectKey、rag:file.objectKey"],
            ["smartnotes/", "智能笔记 PDF 导出文件。", "note:{id}.objectKey / file"],
            ["podcasts/{pid}/", "播客脚本关联音频文件。", "podcast:{pid}.file / static"],
            ["lesson_plans/{id}/", "教案导出 PDF。", "lesson_plan:{id} 及对象 key"],
            ["papers/{id}/", "试卷导出 PDF。", "paper:{id} 及对象 key"],
            ["slides/{id}/", "课件 PPTX 文件和相关资源。", "slide:{id}.pptxObjectKey"],
            ["teaching_videos/{id}/", "教学视频、本地合成音频及脚本结果。", "video:{id}:local_path / audio_path"],
        ],
        caption="表3-10 对象存储目录设计",
        font_size=8.5,
    )

    add_heading(selection, doc, "4 运用设计", 1)
    add_heading(selection, doc, "4.1 数据字典设计", 2)
    add_table(selection, doc, DATA_DICTIONARY, caption="表4-1 数据字典", font_size=8.5)
    add_paragraph(
        selection,
        doc,
        "文档解析支持可抽取文本的 PDF、DOCX、PPTX、XLSX、TXT、Markdown、CSV、JSON 和 HTML。扫描版 PDF 和旧二进制 Office 文件在 RAG 状态中标记为 failed 或 unsupported，不影响其他已选文件继续参与 agent 上下文。",
    )

    add_heading(selection, doc, "4.2 安全保密设计", 2)
    add_table(selection, doc, SECURITY_ITEMS, caption="表4-2 安全保密设计", font_size=8.5)

    add_heading(selection, doc, "4.3 备份与恢复设计", 2)
    add_numbered_lines(
        selection,
        doc,
        [
            "1）PostgreSQL 使用 postgres-data 卷保存认证、KV 和向量数据，可通过 pg_dump/pg_restore 或卷快照备份恢复。",
            "2）MinIO 使用 minio-data 卷保存上传文件和导出物，备份时与 PostgreSQL 保持同一时间窗口。",
            "3）Redis 主要承载任务队列、事件和租约，任务结果以 PostgreSQL/ObjectStore 为准，Redis 可按运行策略恢复。",
            "4）旧 JSON/本地对象数据通过 scripts/migrate_storage_to_adapters.py 迁移到当前 KV/ObjectStore 适配器。",
            "5）RAG 索引可由 rag:file 状态和 file_meta 快照重建；当向量表损坏或迁移后维度变化时，按文件重新索引。",
        ],
    )

    add_heading(selection, doc, "4.4 性能和容量设计", 2)
    add_numbered_lines(
        selection,
        doc,
        [
            "1）认证和聊天索引走关系表，按 user_id、updated_at 和 chat_id 建索引，满足常用列表和详情查询。",
            "2）业务生成结果以 JSONB 存储，减少频繁 schema 迁移；大文件和导出物不进入数据库正文，统一保存到 ObjectStore。",
            "3）RAG 文档按约 900 字符分段并保留约 120 字符重叠，检索时按文件 namespace 控制范围。",
            "4）agent 调用前先检索与 query 相关的分段，再按上下文预算合并，避免第一个大文件挤占全部材料窗口。",
            "5）长任务通过 Celery/Redis 调度，生成服务可以水平扩展 worker 数量，数据库通过连接池和索引控制负载。",
        ],
    )

    add_heading(selection, doc, "4.5 数据维护规则", 2)
    add_numbered_lines(
        selection,
        doc,
        [
            "1）删除文件时同步删除 ObjectStore 原始对象、file_meta、rag:file 状态和 file:{file_id} 向量 namespace。",
            "2）删除用户时依赖认证表级联删除会话和聊天索引，并由业务清理流程删除用户维度 KV 和对象文件。",
            "3）生成任务失败时保留 error 字段和状态，前端展示友好提示，后端保留诊断信息便于定位。",
            "4）RAG 检索或 embedding 服务短时不可用时，agent 使用公平多文件原文片段兜底，保证核心业务连续。",
            "5）生产环境中的数据库密码、S3 密钥和模型密钥只在部署环境配置，不写入源码和文档附件。",
        ],
    )


def fill_cover(doc) -> None:
    replacements = {
        "XXX技术有限公司": COMPANY,
        "XXX 技术有限公司": COMPANY,
        "XXXX系统": SYSTEM_NAME,
        "XXXX 系统": SYSTEM_NAME,
        "XXXXX系统": SYSTEM_NAME,
        "XXX数据库设计说明书": DOC_NAME,
        "XXX 数据库设计说明书": DOC_NAME,
        "《XXXX》": f"《{SYSTEM_NAME}》",
        "文件编号：": f"文件编号：{DOC_NO}",
        "编 制 人：": f"编 制 人：{AUTHOR}",
        "编制日期：": f"编制日期：{DOC_DATE}",
        "审 核 人：": f"审 核 人：{REVIEWER}",
    }
    for old, new in replacements.items():
        replace_all(doc, old, new)
    for paragraph in doc.Paragraphs:
        text = clean_text(paragraph.Range.Text)
        if any(label in text for label in ["文件名称：", "文件编号：", "编 制 人：", "编制日期：", "审 核 人："]):
            try:
                paragraph.Range.ParagraphFormat.OutlineLevel = WD_OUTLINE_LEVEL_BODY_TEXT
                paragraph.Range.Style = doc.Styles(WD_STYLE_NORMAL)
            except Exception:
                continue


def update_fields(doc) -> None:
    try:
        doc.Repaginate()
    except Exception:
        pass
    try:
        for index in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents(index).Update()
    except Exception:
        pass
    try:
        doc.Fields.Update()
    except Exception:
        pass


def generate() -> dict[str, Any]:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}")
    prepare_copy()
    word = start_word()
    try:
        analysis = analyze_template(word)
        doc = word.Documents.Open(str(OUTPUT_DOC), False, False)
        try:
            fill_cover(doc)
            insert_body(word, doc)
            update_fields(doc)
            doc.SaveAs2(str(OUTPUT_DOC), WD_FORMAT_DOCUMENT)
            doc.SaveAs2(str(OUTPUT_DOCX), WD_FORMAT_XML_DOCUMENT)
            doc.ExportAsFixedFormat(str(OUTPUT_PDF), WD_FORMAT_PDF)
        finally:
            doc.Close(False)
        validation = validate_document(word, analysis)
        return validation
    finally:
        close_word(word)


def validate_document(word, analysis: dict[str, Any]) -> dict[str, Any]:
    doc = word.Documents.Open(str(OUTPUT_DOC), False, True)
    try:
        text = clean_text(doc.Content.Text)
        forbidden = ["不知道", "待补充", "预计完成", "预计", "TBD", "TODO", "XXX", "XXXX", "XXXXX", "SYS_LOG_INFO", "SYS_USER_INFO"]
        required = [
            COMPANY,
            SYSTEM_NAME,
            DOC_NAME,
            AUTHOR,
            REVIEWER,
            "edumind_auth_users",
            "edumind_kv",
            "edumind_vectors",
            "rag:file:{file_id}",
            "file:{file_id}",
            "PostgreSQL 16",
            "pgvector",
            "Redis",
            "MinIO",
        ]
        missing = [item for item in required if item not in text]
        forbidden_found = [item for item in forbidden if item in text]
        result = {
            "output_doc": str(OUTPUT_DOC),
            "output_docx": str(OUTPUT_DOCX),
            "output_pdf": str(OUTPUT_PDF),
            "template": {
                "paragraphs": analysis.get("paragraphs"),
                "tables": len(analysis.get("tables", [])),
                "inlineShapes": analysis.get("inlineShapes"),
                "shapes": len(analysis.get("shapes", [])),
                "pages": analysis.get("pages"),
            },
            "document": {
                "paragraphs": doc.Paragraphs.Count,
                "tables": doc.Tables.Count,
                "pages": doc.ComputeStatistics(2),
                "characters": len(text),
            },
            "missing_required_terms": missing,
            "forbidden_terms_found": forbidden_found,
            "ok": not missing and not forbidden_found and doc.Tables.Count >= 15,
        }
        VALIDATION_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        if not result["ok"]:
            raise RuntimeError(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    finally:
        doc.Close(False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EduMind database design Word document from the provided template.")
    parser.add_argument("--validate-only", action="store_true", help="Validate the existing generated document without rewriting it.")
    args = parser.parse_args()
    if args.validate_only:
        word = start_word()
        try:
            analysis = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))
            result = validate_document(word, analysis)
        finally:
            close_word(word)
    else:
        result = generate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
