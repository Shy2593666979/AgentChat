import threading
from typing import Any
from loguru import logger
from typing_extensions import override

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.messages.ai import UsageMetadata, add_usage
from langchain_core.outputs import ChatGeneration, LLMResult

from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.utils.contexts import get_user_id_context, get_agent_name_context


class UsageMetadataCallbackHandler(BaseCallbackHandler):
    """
    Callback Handler that tracks AIMessage.usage_metadata.
    """

    def __init__(self) -> None:
        """Initialize the UsageMetadataCallbackHandler."""
        super().__init__()
        self._lock = threading.Lock()
        self.usage_metadata: dict[str, UsageMetadata] = {}

    @override
    def __repr__(self) -> str:
        return str(self.usage_metadata)

    @override
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Collect token usage."""
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
                    model_name = message.response_metadata.get("model_name")
            except AttributeError:
                pass

        # update shared state behind lock
        if usage_metadata and model_name:
            with self._lock:
                if model_name not in self.usage_metadata:
                    self.usage_metadata[model_name] = usage_metadata
                else:
                    self.usage_metadata[model_name] = add_usage(
                        self.usage_metadata[model_name], usage_metadata
                    )
                self.record_token_usage(model_name, usage_metadata)

    def record_token_usage(self, model_name, usage_metadata):
        user_id = get_user_id_context()
        agent_name = get_agent_name_context()

        record = {
            'model': model_name,
            "agent": agent_name,
            "user_id": user_id,
            'input_tokens': usage_metadata.get("input_tokens", 0),
            'output_tokens': usage_metadata.get("output_tokens", 0),
        }
        logger.info(f"{model_name} cost input tokens: {usage_metadata.get("input_tokens")}, output tokens: {usage_metadata.get("output_tokens")}")

        UsageStatsService.sync_create_usage_stats(**record)
