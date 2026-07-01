"""
LLM 模型管理模块
支持多个 LLM 提供商：Gemini, OpenAI, Claude, Grok, Ollama, OpenRouter, DeepSeek
"""
import os
from threading import Lock
from typing import Optional, List, Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from config import config


_default_llm_lock = Lock()
_default_embeddings_lock = Lock()
_default_llm: Optional[BaseChatModel] = None
_default_embeddings: Optional[Embeddings] = None


def make_llm(
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
) -> BaseChatModel:
    """根据配置创建 LLM 实例。可选 max_tokens、provider（指定则覆盖全局 LLM_PROVIDER）。"""
    use_provider = (provider or config.llm_provider).lower()
    maxtok = max_tokens if max_tokens is not None else config.llm_maxtok

    if use_provider == "gemini":
        if not config.gemini:
            raise ValueError("GEMINI_API_KEY not set")
        return ChatGoogleGenerativeAI(
            model=config.gemini_model,
            google_api_key=config.gemini,
            temperature=config.llm_temp,
            max_tokens=maxtok,
        )

    elif use_provider == "openai":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        kwargs = {
            "model": config.openai_model,
            "api_key": config.openai_api_key,
            "temperature": config.llm_temp,
            "max_tokens": maxtok,
        }
        # 如果设置了 base_url（用于 DeepSeek 等兼容接口）
        if config.openai_base_url:
            kwargs["base_url"] = config.openai_base_url
        return ChatOpenAI(**kwargs)

    elif use_provider == "claude":
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(
            model=config.claude_model,
            api_key=config.anthropic_api_key,
            temperature=config.llm_temp,
            max_tokens=maxtok,
        )

    elif use_provider == "grok":
        if not config.xai_api_key:
            raise ValueError("XAI_API_KEY not set")
        return ChatOpenAI(
            model=config.grok_model,
            api_key=config.xai_api_key,
            base_url=config.grok_base,
            temperature=config.llm_temp,
            max_tokens=maxtok,
        )

    elif use_provider == "ollama":
        return ChatOllama(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            temperature=config.llm_temp,
        )

    elif use_provider == "deepseek":
        if not config.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")
        return ChatOpenAI(
            model=config.deepseek_model,
            api_key=config.deepseek_api_key,
            base_url=config.deepseek_base_url,
            temperature=config.llm_temp,
            max_tokens=maxtok,
        )

    elif use_provider == "openrouter":
        if not config.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        return ChatOpenAI(
            model=config.openrouter_model,
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=config.llm_temp,
            max_tokens=maxtok,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {use_provider}")


def make_embeddings() -> Embeddings:
    """根据配置创建 Embeddings 实例"""
    provider = config.emb_provider.lower()

    if provider == "openai":
        api_key = config.openai_embed_api_key or config.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not set for embeddings")
        kwargs = {
            "model": config.openai_embed_model,
            "api_key": api_key,
        }
        # 如果设置了 embed base_url
        if config.openai_embed_base_url:
            kwargs["base_url"] = config.openai_embed_base_url
        return OpenAIEmbeddings(**kwargs)

    elif provider == "gemini":
        if not config.gemini:
            raise ValueError("GEMINI_API_KEY not set for embeddings")
        return GoogleGenerativeAIEmbeddings(
            model=config.gemini_embed_model,
            google_api_key=config.gemini,
        )

    elif provider == "ollama":
        if not config.ollama_embed_model:
            raise ValueError("OLLAMA_EMBED_MODEL not set")
        return OllamaEmbeddings(
            model=config.ollama_embed_model,
            base_url=config.ollama_base_url,
        )

    elif provider == "local":
        # 使用本地 Transformers.js 模型
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            class LocalEmbeddings(Embeddings):
                """本地嵌入模型包装器"""

                def __init__(self, model_name: str = None, model_path: str = None):
                    if model_path:
                        self.model = SentenceTransformer(model_path)
                    else:
                        self.model = SentenceTransformer(model_name)

                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    """嵌入文档列表"""
                    embeddings = self.model.encode(
                        texts, convert_to_numpy=True, show_progress_bar=False
                    )
                    return embeddings.tolist()

                def embed_query(self, text: str) -> List[float]:
                    """嵌入查询文本"""
                    embedding = self.model.encode(text, convert_to_numpy=True)
                    return embedding.tolist()

            return LocalEmbeddings(
                model_name=config.local_embed_model,
                model_path=config.local_embed_model_path,
            )
        except ImportError:
            # 如果 sentence_transformers 未安装，使用 Xenova/transformers.js
            try:
                from transformers import AutoTokenizer, AutoModel
                import torch

                class TransformersEmbeddings(Embeddings):
                    """Transformers 本地嵌入模型"""

                    def __init__(self, model_name: str):
                        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                        self.model = AutoModel.from_pretrained(model_name)

                    def embed_documents(self, texts: List[str]) -> List[List[float]]:
                        embeddings = []
                        for text in texts:
                            inputs = self.tokenizer(
                                text, return_tensors="pt", padding=True, truncation=True
                            )
                            with torch.no_grad():
                                outputs = self.model(**inputs)
                            embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
                            embeddings.append(embedding.tolist())
                        return embeddings

                    def embed_query(self, text: str) -> List[List[float]]:
                        inputs = self.tokenizer(
                            text, return_tensors="pt", padding=True, truncation=True
                        )
                        with torch.no_grad():
                            outputs = self.model(**inputs)
                        embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
                        return [embedding.tolist()]

                return TransformersEmbeddings(config.local_embed_model)
            except ImportError:
                raise ImportError(
                    "本地嵌入模型需要安装 sentence-transformers 或 transformers。"
                    "请运行: pip install sentence-transformers"
                )

    else:
        raise ValueError(f"Unknown embeddings provider: {provider}")


def get_llm(
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
) -> BaseChatModel:
    """
    获取 LLM 实例。

    默认 provider/max_tokens 使用缓存，避免在模块导入阶段就初始化所有依赖。
    指定 provider 或 max_tokens 时按需创建临时实例。
    """
    if provider is not None or max_tokens is not None:
        return make_llm(max_tokens=max_tokens, provider=provider)

    global _default_llm
    if _default_llm is None:
        with _default_llm_lock:
            if _default_llm is None:
                _default_llm = make_llm()
    return _default_llm


def get_embeddings() -> Embeddings:
    """
    获取 Embeddings 实例。

    Embeddings 仅在真正需要时初始化，避免本地模型路径问题阻塞整个后端启动。
    """
    global _default_embeddings
    if _default_embeddings is None:
        with _default_embeddings_lock:
            if _default_embeddings is None:
                _default_embeddings = make_embeddings()
    return _default_embeddings


async def invoke_llm(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
) -> str:
    """
    调用 LLM 的便捷函数。

    Args:
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        max_tokens: 可选，指定本次调用的最大输出 token
        provider: 可选，指定 LLM 提供商（如 "deepseek"），不传则用全局 LLM_PROVIDER

    Returns:
        LLM 响应文本
    """
    mode = (config.llm_execution_mode or "local").strip().lower()
    service_name = os.environ.get("SERVICE_NAME", "").strip().lower()
    if mode == "remote" and service_name != "ai-core":
        return await invoke_llm_remote(messages, max_tokens=max_tokens, provider=provider)
    return await invoke_llm_local(messages, max_tokens=max_tokens, provider=provider)


async def invoke_llm_remote(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
) -> str:
    import httpx

    payload: Dict[str, Any] = {"messages": messages}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if provider:
        payload["provider"] = provider

    headers: Dict[str, str] = {}
    if config.internal_service_token:
        headers["X-Internal-Service-Token"] = config.internal_service_token

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{config.ai_core_service_url.rstrip('/')}/ai/internal/invoke",
            json=payload,
            headers=headers,
        )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not data.get("ok"):
        raise RuntimeError(str(data.get("error") if isinstance(data, dict) else "AI Core request failed"))
    return str(data.get("text") or "")


async def invoke_llm_local(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
) -> str:
    """Invoke the configured LLM provider in the current process."""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    lc_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))

    if provider is not None:
        model = make_llm(max_tokens=max_tokens, provider=provider)
    else:
        model = get_llm(max_tokens=max_tokens)
    response = await model.ainvoke(lc_messages)

    # 处理不同类型的响应
    if hasattr(response, "content"):
        return str(response.content)
    else:
        return str(response)
