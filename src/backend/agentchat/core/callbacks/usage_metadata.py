import threading
from collections import OrderedDict
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.messages.ai import UsageMetadata, add_usage
from langchain_core.outputs import ChatGeneration, LLMResult
from loguru import logger
from typing_extensions import override

from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.database import SystemUser
from agentchat.utils.contexts import (
    get_agent_name_context,
    get_conversation_id_context,
    get_user_id_context,
)
from agentchat.utils.logging import record_model_usage


class UsageMetadataCallbackHandler(BaseCallbackHandler):
    """
    Callback Handler that tracks AIMessage.usage_metadata.
    """

    def __init__(self) -> None:
        """Initialize the UsageMetadataCallbackHandler."""
        super().__init__()
        self._lock = threading.Lock()
        self.usage_metadata: dict[str, UsageMetadata] = {}
        self._recorded_runs: OrderedDict[str, None] = OrderedDict()

    @override
    def __repr__(self) -> str:
        return str(self.usage_metadata)

    @override
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """收集供应方实际返回的用量，并关联当前用户和会话。"""
        output = response.llm_output or {}
        # 自定义模型已直接写入用量时，不再通过回调重复记录。
        if output.get("usage_recorded"):
            return
        # Check for usage_metadata (langchain-core >= 0.2.2)
        try:
            generation = response.generations[0][0]
        except IndexError:
            generation = None

        usage_metadata = None
        model_name = None
        if isinstance(generation, ChatGeneration):
            try:
                message = generation.message
                if isinstance(message, AIMessage):
                    usage_metadata = message.usage_metadata
                    model_name = message.response_metadata.get("model_name") or message.response_metadata.get("model")
            except AttributeError:
                pass

        model_name = model_name or output.get("model_name") or output.get("model")
        raw_usage = output.get("token_usage") or output.get("usage")
        if not usage_metadata and isinstance(raw_usage, dict) and any(
            key in raw_usage for key in ("prompt_tokens", "completion_tokens", "input_tokens", "output_tokens")
        ):
            input_tokens = max(0, int(raw_usage.get("prompt_tokens", raw_usage.get("input_tokens", 0)) or 0))
            output_tokens = max(0, int(raw_usage.get("completion_tokens", raw_usage.get("output_tokens", 0)) or 0))
            usage_metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }

        # 同一模型调用只记一次；限制去重缓存大小，避免长期运行时不断占用内存。
        if usage_metadata and model_name:
            with self._lock:
                run_id = str(kwargs["run_id"]) if kwargs.get("run_id") else None
                if run_id and run_id in self._recorded_runs:
                    return
                try:
                    self.record_token_usage(model_name, usage_metadata)
                except Exception as error:
                    logger.warning("模型用量记录失败，不影响回复：{}", type(error).__name__)
                    return
                if model_name not in self.usage_metadata:
                    self.usage_metadata[model_name] = usage_metadata
                else:
                    self.usage_metadata[model_name] = add_usage(
                        self.usage_metadata[model_name], usage_metadata
                    )
                if run_id:
                    self._recorded_runs[run_id] = None
                    if len(self._recorded_runs) > 4096:
                        self._recorded_runs.popitem(last=False)

    def record_token_usage(self, model_name, usage_metadata):
        user_id = get_user_id_context()
        agent_name = get_agent_name_context()

        record = {
            'model': model_name,
            "agent": agent_name,
            "user_id": user_id or SystemUser,
            "conversation_id": get_conversation_id_context(),
            'input_tokens': usage_metadata.get("input_tokens", 0),
            'output_tokens': usage_metadata.get("output_tokens", 0),
        }
        UsageStatsService.sync_create_usage_stats(**record)
        record_model_usage(model_name, record["input_tokens"], record["output_tokens"])
