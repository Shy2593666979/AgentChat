from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from agentchat.core.models.embedding import EmbeddingModel
from agentchat.core.models.tool_call import ToolCallModel
from agentchat.core.models.reason_model import ReasoningModel
from agentchat.settings import app_settings



class ModelManager:

    @classmethod
    def get_tool_invocation_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=app_settings.multi_models.tool_call_model.model_name,
            api_key=app_settings.multi_models.tool_call_model.api_key,
            base_url=app_settings.multi_models.tool_call_model.base_url)

    @classmethod
    def get_conversation_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=app_settings.multi_models.conversation_model.model_name,
            api_key=app_settings.multi_models.conversation_model.api_key,
            base_url=app_settings.multi_models.conversation_model.base_url)

    @classmethod
    def get_reasoning_model(cls) -> ReasoningModel:
        return ReasoningModel(model_name=app_settings.multi_models.reasoning_model.model_name,
                              api_key=app_settings.multi_models.reasoning_model.api_key,
                              base_url=app_settings.multi_models.reasoning_model.base_url)

    @classmethod
    def get_lingseek_intent_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=app_settings.multi_models.tool_call_model.model_name,
            api_key=app_settings.multi_models.tool_call_model.api_key,
            base_url=app_settings.multi_models.tool_call_model.base_url)

    @classmethod
    def get_qwen_vl_model(cls) -> BaseChatModel:
        return ChatOpenAI(model=app_settings.multi_models.qwen_vl.model_name,
                          api_key=app_settings.multi_models.qwen_vl.api_key,
                          base_url=app_settings.multi_models.qwen_vl.base_url)

    @classmethod
    def get_user_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=kwargs.get("model"),
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"))

    @classmethod
    def get_embedding_model(cls) -> EmbeddingModel:
        return EmbeddingModel(
            model=app_settings.multi_models.embedding.model_name,
            base_url=app_settings.multi_models.embedding.base_url,
            api_key=app_settings.multi_models.embedding.api_key
        )
