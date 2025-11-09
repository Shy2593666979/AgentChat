from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from agentchat.core.models.manager import ModelManager


class StructuredResponseAgent:
    def __init__(self, response_format):
        self.response_format = response_format
        self.structured_agent = self._create_structured_agent()

    def _create_structured_agent(self):
        return create_agent(
            model=ModelManager.get_conversation_model(),
            response_format=ToolStrategy(self.response_format)
        )

    def get_structured_response(self, messages):
        result = self.structured_agent.invoke({"messages": messages})
        return result["structured_response"]