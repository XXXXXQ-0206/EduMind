"""
配置管理模块
从环境变量加载配置，与原 Node.js 版本保持兼容
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""

    # 服务器配置
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=5000, alias="PORT")
    backend_url: str = Field(default="http://localhost:5000", alias="VITE_BACKEND_URL")
    frontend_url: str = Field(default="http://localhost:5173", alias="VITE_FRONTEND_URL")
    timeout: int = Field(default=90000, alias="VITE_TIMEOUT")

    # 数据库配置
    db_mode: str = Field(default="json", alias="db_mode")
    kv_store_provider: str = Field(default="json", alias="KV_STORE_PROVIDER")
    postgres_dsn: str = Field(
        default="postgresql://edumind:edumind@postgres:5432/edumind",
        alias="POSTGRES_DSN",
    )
    object_store_provider: str = Field(default="local", alias="OBJECT_STORE_PROVIDER")
    object_store_base_url: str = Field(default="/storage", alias="OBJECT_STORE_BASE_URL")
    event_bus_provider: str = Field(default="memory", alias="EVENT_BUS_PROVIDER")
    task_lease_provider: str = Field(default="kv", alias="TASK_LEASE_PROVIDER")
    task_lease_ttl_seconds: int = Field(default=1800, alias="TASK_LEASE_TTL_SECONDS")
    task_queue_provider: str = Field(default="inline", alias="TASK_QUEUE_PROVIDER")
    task_queue_name: str = Field(default="edumind:tasks", alias="TASK_QUEUE_NAME")
    task_worker_poll_seconds: float = Field(default=2.0, alias="TASK_WORKER_POLL_SECONDS")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")
    celery_task_queue_name: str = Field(default="edumind:generation", alias="CELERY_TASK_QUEUE_NAME")
    celery_visibility_timeout_seconds: int = Field(default=3600, alias="CELERY_VISIBILITY_TIMEOUT_SECONDS")
    celery_task_max_retries: int = Field(default=3, alias="CELERY_TASK_MAX_RETRIES")
    celery_task_retry_delay_seconds: int = Field(default=10, alias="CELERY_TASK_RETRY_DELAY_SECONDS")
    celery_worker_concurrency: int = Field(default=2, alias="CELERY_WORKER_CONCURRENCY")
    celery_worker_pool: str = Field(default="prefork", alias="CELERY_WORKER_POOL")
    s3_endpoint_url: Optional[str] = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_bucket: str = Field(default="edumind", alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_access_key_id: Optional[str] = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: Optional[str] = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_cache_dir: Optional[Path] = Field(default=None, alias="S3_CACHE_DIR")

    # 微服务内部通信配置
    auth_validation_mode: str = Field(default="local", alias="AUTH_VALIDATION_MODE")
    identity_service_url: str = Field(default="http://127.0.0.1:5101", alias="IDENTITY_URL")
    internal_service_token: Optional[str] = Field(default=None, alias="INTERNAL_SERVICE_TOKEN")
    ai_core_service_url: str = Field(default="http://127.0.0.1:5106", alias="AI_CORE_URL")
    llm_execution_mode: str = Field(default="local", alias="LLM_EXECUTION_MODE")

    # LLM 核心设置
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    emb_provider: str = Field(default="openai", alias="EMB_PROVIDER")
    llm_temp: float = Field(default=1.0, alias="LLM_TEMP")
    llm_maxtok: int = Field(default=16384, alias="LLM_MAXTOK")

    # Gemini 配置
    gemini: Optional[str] = Field(default=None, alias="gemini")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="gemini_model")
    gemini_embed_model: str = Field(default="text-embedding-004", alias="gemini_embed_model")

    # OpenAI 配置
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    openai_embed_api_key: Optional[str] = Field(default=None, alias="OPENAI_EMBED_API_KEY")
    openai_embed_model: str = Field(default="text-embedding-3-large", alias="OPENAI_EMBED_MODEL")
    openai_embed_base_url: Optional[str] = Field(default=None, alias="OPENAI_EMBED_BASE_URL")

    # Claude 配置
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-3-5-sonnet-latest", alias="CLAUDE_MODEL")

    # DeepSeek 配置
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")

    # 播客脚本生成专用 LLM（默认使用 DeepSeek 做深度讨论）
    podcast_llm_provider: str = Field(default="deepseek", alias="PODCAST_LLM_PROVIDER")

    # OpenRouter 配置
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="google/gemini-2.5-flash", alias="OPENROUTER_MODEL")

    # Grok 配置
    xai_api_key: Optional[str] = Field(default=None, alias="XAI_API_KEY")
    grok_model: str = Field(default="grok-2-latest", alias="GROK_MODEL")
    grok_base: str = Field(default="https://api.x.ai/v1", alias="GROK_BASE")

    # Ollama 配置
    ollama_model: str = Field(default="llama4", alias="OLLAMA_MODEL")
    ollama_embed_model: str = Field(default="", alias="OLLAMA_EMBED_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    # Local Embedding 配置
    local_embed_model: str = Field(default="Xenova/all-MiniLM-L6-v2", alias="LOCAL_EMBED_MODEL")
    local_embed_model_path: Optional[str] = Field(default=None, alias="LOCAL_EMBED_MODEL_PATH")

    # TTS 配置
    tts_provider: str = Field(default="edge", alias="TTS_PROVIDER")
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    tts_voice_edge: str = Field(default="en-US-AvaNeural", alias="TTS_VOICE_EDGE")
    tts_voice_alt_edge: str = Field(default="en-US-AndrewNeural", alias="TTS_VOICE_ALT_EDGE")
    tts_voice_edge_en_us: str = Field(default="en-US-AvaNeural", alias="TTS_VOICE_EDGE_EN_US")
    tts_voice_edge_en_gb: str = Field(default="en-GB-LibbyNeural", alias="TTS_VOICE_EDGE_EN_GB")
    eleven_api_key: Optional[str] = Field(default=None, alias="ELEVEN_API_KEY")
    eleven_voice_a: str = Field(default="", alias="ELEVEN_VOICE_A")
    eleven_voice_b: str = Field(default="", alias="ELEVEN_VOICE_B")
    google_credentials: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    tts_voice_google: str = Field(default="en-US-Neural2-F", alias="TTS_VOICE_GOOGLE")
    tts_voice_alt_google: str = Field(default="en-US-Neural2-D", alias="TTS_VOICE_ALT_GOOGLE")

    # 转录配置
    transcription_provider: str = Field(default="openai", alias="TRANSCRIPTION_PROVIDER")
    assemblyai_api_key: Optional[str] = Field(default=None, alias="ASSEMBLYAI_API_KEY")
    google_cloud_project_id: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT_ID")
    transcription_openai_api_key: Optional[str] = Field(default=None, alias="TRANSCRIPTION_OPENAI_API_KEY")
    transcription_openai_base_url: Optional[str] = Field(default=None, alias="TRANSCRIPTION_OPENAI_BASE_URL")
    transcription_openai_model: str = Field(default="gpt-4o-mini-transcribe", alias="TRANSCRIPTION_OPENAI_MODEL")
    transcription_language: Optional[str] = Field(default=None, alias="TRANSCRIPTION_LANGUAGE")

    # Xunfei ISE (Speech Evaluation)
    xfyun_appid: Optional[str] = Field(default=None, alias="XFYUN_APPID")
    xfyun_api_secret: Optional[str] = Field(default=None, alias="XFYUN_API_SECRET")
    xfyun_api_key: Optional[str] = Field(default=None, alias="XFYUN_API_KEY")

    # 即梦 AI（火山引擎）图像生成
    jimeng_access_key_id: Optional[str] = Field(default=None, alias="JIMENG_ACCESS_KEY_ID")
    jimeng_secret_access_key: Optional[str] = Field(default=None, alias="JIMENG_SECRET_ACCESS_KEY")

    # 即梦 视频生成（火山方舟 文生视频 3.0 1080P）
    jimeng_video_provider: str = Field(default="auto", alias="JIMENG_VIDEO_PROVIDER")
    jimeng_video_ark_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        alias="JIMENG_VIDEO_ARK_BASE_URL",
    )
    jimeng_video_ark_api_key: Optional[str] = Field(default=None, alias="JIMENG_VIDEO_ARK_API_KEY")
    jimeng_video_model: Optional[str] = Field(default=None, alias="JIMENG_VIDEO_MODEL")  # 推理接入点 Endpoint ID
    jimeng_video_gateway_base_url: str = Field(
        default="https://ai-gateway.vei.volces.com/v1/contents/generations/tasks",
        alias="JIMENG_VIDEO_GATEWAY_BASE_URL",
    )
    jimeng_video_gateway_api_key: Optional[str] = Field(default=None, alias="JIMENG_VIDEO_GATEWAY_API_KEY")
    jimeng_video_student_type: str = Field(default="mixed_age", alias="JIMENG_VIDEO_STUDENT_TYPE")
    jimeng_video_teaching_style: str = Field(default="vivid_fun", alias="JIMENG_VIDEO_TEACHING_STYLE")
    jimeng_video_voice_type: str = Field(
        default="zh_female_linjianvhai_moon_bigtts",
        alias="JIMENG_VIDEO_VOICE_TYPE",
    )
    jimeng_video_allow_fallback: bool = Field(default=True, alias="JIMENG_VIDEO_ALLOW_FALLBACK")

    # 存储路径
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    storage_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "storage")

    class Config:
        # 同时从当前项目目录和上级目录加载 .env，确保 DEEPSEEK 等密钥能被读到
        _base = Path(__file__).resolve().parent.parent
        env_file = [
            _base / ".env",
            _base.parent / ".env",
        ]
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


# 全局配置实例
config = Settings()

# 确保存储目录存在（使用绝对路径，避免工作目录影响）
config.storage_dir = config.storage_dir.resolve()
config.storage_dir.mkdir(parents=True, exist_ok=True)
(config.storage_dir / "smartnotes").mkdir(exist_ok=True)
(config.storage_dir / "podcasts").mkdir(exist_ok=True)
(config.storage_dir / "uploads").mkdir(exist_ok=True)
(config.storage_dir / "flashcards").mkdir(exist_ok=True)
(config.storage_dir / "speaking").mkdir(exist_ok=True)
(config.storage_dir / "slides").mkdir(exist_ok=True)
(config.storage_dir / "teaching_videos").mkdir(exist_ok=True)
