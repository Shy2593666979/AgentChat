from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from agentchat.core.models.embedding import EmbeddingModel
from agentchat.core.models.reason_model import ReasoningModel
from agentchat.settings import app_settings


class ModelManager:

    @classmethod
    def get_tool_invocation_model(cls, **kwargs) -> BaseChatModel:
        tool_call_model = app_settings.multi_models.tool_call_model

        return ChatOpenAI(
            stream_usage=True,
            model=tool_call_model.model_name,
            api_key=tool_call_model.api_key,
            base_url=tool_call_model.base_url
        )

    @classmethod
    def get_conversation_model(cls, **kwargs) -> BaseChatModel:
        conversation_model = app_settings.multi_models.conversation_model

        return ChatOpenAI(
            stream_usage=True,
            model=conversation_model.model_name,
            api_key=conversation_model.api_key,
            base_url=conversation_model.base_url
        )

    @classmethod
    def get_reasoning_model(cls) -> ReasoningModel:
        reasoning_model = app_settings.multi_models.reasoning_model

        return ReasoningModel(
            model_name=reasoning_model.model_name,
            api_key=reasoning_model.api_key,
            base_url=reasoning_model.base_url
        )

    @classmethod
    def get_lingseek_intent_model(cls, **kwargs) -> BaseChatModel:
        lingseek_intent_model = app_settings.multi_models.tool_call_model

        return ChatOpenAI(
            stream_usage=True,
            model=lingseek_intent_model.model_name,
            api_key=lingseek_intent_model.api_key,
            base_url=lingseek_intent_model.base_url
        )

    @classmethod
    def get_qwen_vl_model(cls) -> BaseChatModel:
        qwen_vl_model = app_settings.multi_models.qwen_vl

        return ChatOpenAI(
            stream_usage=True,
            model=qwen_vl_model.model_name,
            api_key=qwen_vl_model.api_key,
            base_url=qwen_vl_model.base_url
        )

    @classmethod
    def get_user_model(cls, **kwargs) -> BaseChatModel:
        user_model = kwargs

        return ChatOpenAI(
            stream_usage=True,
            model=user_model.get("model"),
            api_key=user_model.get("api_key"),
            base_url=user_model.get("base_url")
        )

    @classmethod
    def get_embedding_model(cls) -> EmbeddingModel:
        embedding_model = app_settings.multi_models.embedding

        return EmbeddingModel(
            model=embedding_model.model_name,
            base_url=embedding_model.base_url,
            api_key=embedding_model.api_key
        )
