import asyncio
import inspect
import json
from typing import List, Optional

from langgraph.prebuilt.tool_node import ToolCallRequest
from loguru import logger

from pydantic import BaseModel
from langchain_core.messages import ToolMessage, BaseMessage, AIMessage, SystemMessage, ToolCall, HumanMessage, \
    AIMessageChunk
from langchain_core.tools import BaseTool
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState

from langchain.agents import create_agent
from langchain.agents.middleware import AgentState, wrap_model_call, wrap_tool_call, after_model, \
    LLMToolSelectorMiddleware, before_agent, ModelRequest

from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function

from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.chat import DEFAULT_CALL_PROMPT
from agentchat.services.mcp.manager import MCPManager
from agentchat.utils.helpers import fix_json_text
from agentchat.utils.convert import convert_mcp_config


class MCPConfig(BaseModel):
    url: str
    type: str = "sse"
    tools: List[str] = []
    server_name: str
    mcp_server_id: str


class MCPAgent:
    def __init__(self, mcp_config: MCPConfig, user_id: str, agent_name=None):
        self.mcp_config = mcp_config
        self.mcp_manager = MCPManager([convert_mcp_config(mcp_config.model_dump())])

        self.agent_name = agent_name
        self.user_id = user_id
        self.mcp_tools: List[BaseTool] = []
        self.conversation_model = None
        self.tool_invocation_model = None
        self.graph = None
        self.step_counter = 0
        self.step_counter_lock = asyncio.Lock()

    async def init_mcp_agent(self):
        if self.mcp_config:
            self.mcp_tools = await self.set_mcp_tools()

        await self.set_language_model()

        self.middlewares = await self._set_agent_middlewares()

        self._agent = self._set_graph_agent()

    async def set_language_model(self):
        # 普通对话模型
        self.conversation_model = ModelManager.get_conversation_model()

        # 支持Function Call模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

    async def set_mcp_tools(self):
        mcp_tools = await self.mcp_manager.get_mcp_tools()
        return mcp_tools

    async def _set_agent_middlewares(self):

        @wrap_tool_call
        async def add_tool_call_args(
            request: ToolCallRequest,
            handler
        ):
            # 针对鉴权的MCP Server需要用户的单独配置，例如飞书、邮箱
            mcp_config = await MCPUserConfigService.get_mcp_user_config(self.user_id, self.mcp_config.mcp_server_id)
            request.tool_call["args"].update(mcp_config)

            tool_result = await handler(request)
            return tool_result

        @before_agent
        async def add_agent_system_message(
            state: AgentState,
            runtime
        ):
            state["messages"].insert(0, SystemMessage(content=DEFAULT_CALL_PROMPT))
            return {
                "messages": state["messages"]
            }

        return [add_agent_system_message, add_tool_call_args]

    def _set_graph_agent(self):
        return create_agent(
            model=self.conversation_model,
            tools=self.mcp_tools,
            middleware=self.middlewares
        )


    async def ainvoke(self, messages: List[BaseMessage]) -> List[BaseMessage] | str:
        """非流式版本"""
        result = await self._agent.ainvoke({"messages": messages})
        messages = []
        for message in result["messages"][:-1]: # 去除没有命中工具的AIMessage
            if not isinstance(message, HumanMessage) and not isinstance(message, SystemMessage):
                messages.append(message)
        return messages
        # 是否需要模型总结信息（增加10-20s的时间） ↓
        # return await self.conversation_model.ainvoke(result["messages"][:-1])

    async def _record_agent_token_usage(self, response: AIMessage | AIMessageChunk, model):
        if response.usage_metadata:
            await UsageStatsService.create_usage_stats(
                model=model,
                user_id=self.user_id,
                agent=self.agent_name,
                input_tokens=response.usage_metadata.get("input_tokens"),
                output_tokens=response.usage_metadata.get("output_tokens")
            )

    def find_mcp_tool(self, name) -> BaseTool | None:
        for tool in self.mcp_tools:
            if tool.name == name:
                return tool
        return None





