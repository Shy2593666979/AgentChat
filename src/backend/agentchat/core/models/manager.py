from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from agentchat.settings import app_settings


class ModelManager:

    @classmethod
    def get_tool_invocation_model(cls) -> BaseChatModel:
        return ChatOpenAI(model_name=app_settings.multi_models.deepseek_v3.model_name,
                          openai_api_key=app_settings.multi_models.deepseek_v3.api_key,
                          openai_api_base=app_settings.multi_models.deepseek_v3.base_url)

    @classmethod
    def get_conversation_model(cls) -> BaseChatModel:
        return ChatOpenAI(model_name=app_settings.multi_models.qwen2.model_name,
                          openai_api_key=app_settings.multi_models.qwen2.api_key,
                          openai_api_base=app_settings.multi_models.qwen2.base_url)

    @classmethod
    def get_reasoning_model(cls) -> BaseChatModel:
        return ChatOpenAI(model_name=app_settings.multi_models.deepseek_r1.model_name,
                          openai_api_key=app_settings.multi_models.deepseek_r1.api_key,
                          openai_api_base=app_settings.multi_models.deepseek_r1.base_url)

    @classmethod
    def get_qwen_vl_model(cls) -> BaseChatModel:
        return ChatOpenAI(model_name=app_settings.multi_models.qwen_vl.model_name,
                          openai_api_key=app_settings.multi_models.qwen_vl.api_key,
                          openai_api_base=app_settings.multi_models.qwen_vl.base_url)
