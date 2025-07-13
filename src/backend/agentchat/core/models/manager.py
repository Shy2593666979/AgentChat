from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from agentchat.core.models.models import ToolCallModel
from agentchat.settings import app_settings


class ModelManager:

    @classmethod
    def get_tool_invocation_model(cls) -> ToolCallModel:
        # return ToolCallModel(model_name=app_settings.multi_models.qwen2.model_name,
        #                      api_key=app_settings.multi_models.qwen2.api_key,
        #                      base_url=app_settings.multi_models.qwen2.base_url)
        return ToolCallModel(model_name=app_settings.multi_models.deepseek_v3.model_name,
                             api_key=app_settings.multi_models.deepseek_v3.api_key,
                             base_url=app_settings.multi_models.deepseek_v3.base_url)

    @classmethod
    def get_conversation_model(cls) -> BaseChatModel:
        return ChatOpenAI(model=app_settings.multi_models.qwen2.model_name,
                          api_key=app_settings.multi_models.qwen2.api_key,
                          base_url=app_settings.multi_models.qwen2.base_url)

    @classmethod
    def get_reasoning_model(cls) -> BaseChatModel:
        return ChatOpenAI(model=app_settings.multi_models.deepseek_r1.model_name,
                          api_key=app_settings.multi_models.deepseek_r1.api_key,
                          base_url=app_settings.multi_models.deepseek_r1.base_url)

    @classmethod
    def get_qwen_vl_model(cls) -> BaseChatModel:
        return ChatOpenAI(model=app_settings.multi_models.qwen_vl.model_name,
                          api_key=app_settings.multi_models.qwen_vl.api_key,
                          base_url=app_settings.multi_models.qwen_vl.base_url)

    @classmethod
    def get_user_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(model=kwargs.get("model"),
                          api_key=kwargs.get("api_key"),
                          base_url=kwargs.get("base_url"))
