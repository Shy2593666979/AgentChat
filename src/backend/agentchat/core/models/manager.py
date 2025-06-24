from langchain_core.language_models import BaseChatModel
from langchain_openai.chat_models import ChatOpenAI

class ModelManager:


    @classmethod
    def get_tool_invocation_model(cls) -> BaseChatModel:
        pass

    @classmethod
    def get_conversation_model(cls) -> BaseChatModel:
        pass

    @classmethod
    def get_reasoning_model(cls) -> BaseChatModel:
        pass