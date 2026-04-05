"""
Agent 基类和通用接口
定义所有 Agent 的基础功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class AgentInput(BaseModel):
    """Agent 输入基类"""
    pass


class AgentOutput(BaseModel):
    """Agent 输出基类"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Agent 基类
    所有具体的 Agent 都应该继承这个类
    """

    def __init__(self, name: str):
        self.name = name
        self.description = ""

    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        执行 Agent 的主要逻辑

        Args:
            input_data: 输入数据

        Returns:
            AgentOutput: 输出结果
        """
        pass

    async def stream_execute(
        self, input_data: AgentInput, on_chunk: callable
    ) -> AgentOutput:
        """
        流式执行 Agent 逻辑（可选实现）

        Args:
            input_data: 输入数据
            on_chunk: 回调函数，接收每个生成的文本块

        Returns:
            AgentOutput: 最终输出结果
        """
        # 默认实现：直接调用 execute
        return await self.execute(input_data)

    def get_info(self) -> Dict[str, str]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "description": self.description,
        }


class LLMAgent(BaseAgent):
    """
    基于 LLM 的 Agent 基类
    提供通用的 LLM 调用能力
    """

    def __init__(self, name: str, system_prompt: str = ""):
        super().__init__(name)
        self.system_prompt = system_prompt

    async def call_llm(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        expect_json: bool = False,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        调用 LLM

        Args:
            user_message: 用户消息
            system_prompt: 系统提示（可选，默认使用 self.system_prompt）
            expect_json: 是否期望 JSON 输出
            max_tokens: 可选，本次调用最大输出 token 数（如 16384 用于长输出）

        Returns:
            LLM 响应文本
        """
        from utils.llm import invoke_llm

        sys_prompt = system_prompt or self.system_prompt

        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": user_message})

        response = await invoke_llm(messages, max_tokens=max_tokens)

        # 如果期望 JSON，尝试清理响应
        if expect_json:
            response = self._extract_json(response)

        return response

    async def call_llm_with_provider(
        self,
        provider: str,
        user_message: str,
        system_prompt: Optional[str] = None,
        expect_json: bool = False,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        使用指定 provider 调用 LLM（如播客脚本专用 DeepSeek）。

        Args:
            provider: LLM 提供商名称，如 "deepseek"
            user_message: 用户消息
            system_prompt: 系统提示（可选）
            expect_json: 是否期望 JSON 输出
            max_tokens: 可选最大输出 token 数

        Returns:
            LLM 响应文本
        """
        from utils.llm import invoke_llm

        sys_prompt = system_prompt or self.system_prompt

        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": user_message})

        response = await invoke_llm(
            messages, max_tokens=max_tokens, provider=provider
        )

        if expect_json:
            response = self._extract_json(response)

        return response

    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON 对象或数组"""
        import json
        import re

        # 先尝试提取 JSON 数组（因为 quiz 返回的是数组）
        arr_match = re.search(r"\[[\s\S]*\]", text)
        if arr_match:
            return arr_match.group(0)

        # 再尝试提取 JSON 对象
        obj_match = re.search(r"\{[\s\S]*\}", text)
        if obj_match:
            return obj_match.group(0)

        return text

    def safe_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """安全地解析 JSON"""
        import json

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
