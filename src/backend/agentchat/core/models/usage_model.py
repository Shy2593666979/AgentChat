from pydantic import Field, PrivateAttr, SecretStr
from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_openai.chat_models.base import WellKnownTools
from openai import OpenAI, AsyncOpenAI

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from typing import Any, List, Optional, Iterator, AsyncIterator, Dict, Union, Sequence, Callable, Literal

from agentchat.utils.contexts import get_user_id_context, get_agent_name_context
from agentchat.utils.convert import convert_langchain_tool_calls
from agentchat.api.services.usage_stats import UsageStatsService


class ChatModelWithTokenUsage(BaseChatModel):
    """基于BaseChatModel实现的带token记录功能的聊天模型"""

    # 公开的模型配置字段
    model_name: str = Field(default="gpt-3.5-turbo", alias="model")
    temperature: float = Field(default=0.7)
    openai_api_key: SecretStr = Field(default=None, alias="api_key")
    openai_api_base: Optional[str] = Field(default=None, alias="base_url")
    max_tokens: Optional[int] = Field(default=None)

    # 用户私有配置
    user_id: Optional[str] = Field(default=None)
    agent_name: Optional[str] = Field(default=None)
    
    # 私有属性用于存储状态
    _client: Optional[OpenAI] = PrivateAttr(default=None)
    _async_client: Optional[AsyncOpenAI] = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        """初始化 OpenAI 客户端"""
        super().model_post_init(__context)

        api_key = self.openai_api_key.get_secret_value() if self.openai_api_key else None
        base_url = self.openai_api_base

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def _llm_type(self) -> str:
        """返回LLM类型标识"""
        return "chat-model-with-token-usage"

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        """同步生成响应"""
        # 转换消息格式
        openai_messages = self._convert_messages(messages)
        # 调用 OpenAI API
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop,
            **kwargs
        )

        # 记录 token 使用
        self._record_token_usage(response.usage)

        # 构造返回结果
        message = AIMessage(content=response.choices[0].message.content, tool_calls=convert_langchain_tool_calls(response.choices[0].message.tool_calls))
        generation = ChatGeneration(message=message)

        return ChatResult(
            generations=[generation],
            llm_output={
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model_name": response.model,
            }
        )

    async def _agenerate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        """异步生成响应"""
        # 转换消息格式
        openai_messages = self._convert_messages(messages)

        # 调用 OpenAI API
        response = await self._async_client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop,
            **kwargs
        )

        # 记录 token 使用
        self._record_token_usage(response.usage)

        # 构造返回结果
        message = AIMessage(content=response.choices[0].message.content, tool_calls=convert_langchain_tool_calls(response.choices[0].message.tool_calls))
        generation = ChatGeneration(message=message)

        return ChatResult(
            generations=[generation],
            llm_output={
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model_name": response.model,
            }
        )

    def _stream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """同步流式生成"""
        openai_messages = self._convert_messages(messages)

        # 用于累积 token 信息
        input_tokens = 0
        output_tokens = 0

        stream = self._client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop,
            stream=True,
            stream_options={"include_usage": True},  # 启用流式 token 统计
            **kwargs
        )

        for chunk in stream:
            # 提取 token 使用信息
            if hasattr(chunk, 'usage') and chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

            # 生成内容块
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    message_chunk = AIMessageChunk(content=delta.content)
                    yield ChatGenerationChunk(message=message_chunk)

        # 记录 token 使用
        if input_tokens > 0 or output_tokens > 0:
            self._record_token_usage_dict(input_tokens, output_tokens)

    async def _astream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """异步流式生成"""
        openai_messages = self._convert_messages(messages)

        # 用于累积 token 信息
        input_tokens = 0
        output_tokens = 0

        stream = await self._async_client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop,
            stream=True,
            stream_options={"include_usage": True},  # 启用流式 token 统计
            **kwargs
        )

        async for chunk in stream:
            # 提取 token 使用信息
            if hasattr(chunk, 'usage') and chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

            # 生成内容块
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    message_chunk = AIMessageChunk(content=delta.content)
                    yield ChatGenerationChunk(message=message_chunk)

        # 记录 token 使用
        if input_tokens > 0 or output_tokens > 0:
            self._record_token_usage_dict(input_tokens, output_tokens)

    def bind_tools(
        self,
        tools: Sequence[Union[dict[str, Any], type, Callable, BaseTool]],
        *,
        tool_choice: Optional[
            Union[dict, str, Literal["auto", "none", "required", "any"], bool]
        ] = None,
        strict: Optional[bool] = None,
        parallel_tool_calls: Optional[bool] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tool-like objects to this chat model."""

        if parallel_tool_calls is not None:
            kwargs["parallel_tool_calls"] = parallel_tool_calls
        formatted_tools = [
            convert_to_openai_tool(tool, strict=strict) for tool in tools
        ]
        tool_names = []
        for tool in formatted_tools:
            if "function" in tool:
                tool_names.append(tool["function"]["name"])
            elif "name" in tool:
                tool_names.append(tool["name"])
            else:
                pass
        if tool_choice:
            if isinstance(tool_choice, str):
                # tool_choice is a tool/function name
                if tool_choice in tool_names:
                    tool_choice = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                elif tool_choice in WellKnownTools:
                    tool_choice = {"type": tool_choice}
                # 'any' is not natively supported by OpenAI API.
                # We support 'any' since other models use this instead of 'required'.
                elif tool_choice == "any":
                    tool_choice = "required"
                else:
                    pass
            elif isinstance(tool_choice, bool):
                tool_choice = "required"
            elif isinstance(tool_choice, dict):
                pass
            else:
                raise ValueError(
                    f"Unrecognized tool_choice type. Expected str, bool or dict. "
                    f"Received: {tool_choice}"
                )
            kwargs["tool_choice"] = tool_choice
        return super().bind(tools=formatted_tools, **kwargs)

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict]:
        """将 LangChain 消息转换为 OpenAI 格式"""
        openai_messages = []
        for msg in messages:
            if msg.type == "human":
                role = "user"
            elif msg.type == "ai":
                role = "assistant"
            elif msg.type == "system":
                role = "system"
            else:
                role = "user"

            openai_messages.append({
                "role": role,
                "content": msg.content
            })
        return openai_messages

    def _record_token_usage(self, usage: Any):
        """记录 token 使用（从 usage 对象）"""
        self.agent_name = self.agent_name if self.agent_name else get_agent_name_context()
        self.user_id = self.user_id if self.user_id else get_user_id_context()

        if usage and self.user_id:
            record = {
                'model': self.model_name,
                "agent": self.agent_name,
                "user_id": self.user_id,
                'input_tokens': usage.prompt_tokens,
                'output_tokens': usage.completion_tokens,
            }
            UsageStatsService.sync_create_usage_stats(**record)

    def _record_token_usage_dict(self, input_tokens: int, output_tokens: int):
        """记录 token 使用（从原始数值）"""
        self.agent_name = self.agent_name if self.agent_name else get_agent_name_context()
        self.user_id = self.user_id if self.user_id else get_user_id_context()

        if self.user_id:
            record = {
                "model": self.model_name,
                "agent": self.agent_name,
                "user_id": self.user_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
            UsageStatsService.sync_create_usage_stats(**record)
