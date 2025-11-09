from typing import List, Optional
from pydantic import BaseModel

from langchain.tools import BaseTool
from langchain.agents import create_agent
from langgraph.prebuilt.tool_node import ToolCallRequest
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain.agents.middleware import AgentState, wrap_tool_call, before_agent

from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.chat import DEFAULT_CALL_PROMPT
from agentchat.services.mcp.manager import MCPManager
from agentchat.utils.convert import convert_mcp_config


class MCPConfig(BaseModel):
    url: str
    type: str = "sse"
    tools: List[str] = []
    server_name: str
    mcp_server_id: str


class MCPAgent:
    def __init__(self, mcp_config: MCPConfig, user_id: str, emit_event):
        self.mcp_config = mcp_config
        self.mcp_manager = MCPManager([convert_mcp_config(mcp_config.model_dump())])
        self.emit_event = emit_event

        self.user_id = user_id
        self.mcp_tools: List[BaseTool] = []

        self.conversation_model = None
        self.tool_invocation_model = None

        self.react_agent = None
        self.middlewares = None

    async def init_mcp_agent(self):
        if self.mcp_config:
            self.mcp_tools = await self.setup_mcp_tools()

        await self.setup_language_model()

        self.middlewares = await self.setup_agent_middlewares()

        self.react_agent = self.setup_react_agent()

    async def setup_language_model(self):
        # 普通对话模型
        self.conversation_model = ModelManager.get_conversation_model()

        # 工具调用模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

    async def setup_mcp_tools(self):
        mcp_tools = await self.mcp_manager.get_mcp_tools()
        return mcp_tools

    async def setup_agent_middlewares(self):

        @wrap_tool_call
        async def add_tool_call_args(
            request: ToolCallRequest,
            handler
        ):
            await self.emit_event(
                {
                    "status": "START",
                    "title": f"Sub-Agent - {self.mcp_config.server_name}执行可用工具: {request.tool_call["name"]}",
                    "messages": f"正在调用工具 {request.tool_call["name"]}..."
                }
            )

            # 针对鉴权的MCP Server需要用户的单独配置，例如飞书、邮箱
            mcp_config = await MCPUserConfigService.get_mcp_user_config(self.user_id, self.mcp_config.mcp_server_id)
            request.tool_call["args"].update(mcp_config)

            tool_result = await handler(request)

            await self.emit_event(
                {
                    "status": "END",
                    "title": f"Sub-Agent - {self.mcp_config.server_name}执行可用工具: {request.tool_call["name"]}",
                    "messages": f"{tool_result}"
                }
            )
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

    def setup_react_agent(self):
        return create_agent(
            model=self.conversation_model,
            tools=self.mcp_tools,
            middleware=self.middlewares
        )


    async def ainvoke(self, messages: List[BaseMessage]) -> List[BaseMessage] | str:
        """非流式版本"""
        result = await self.react_agent.ainvoke({"messages": messages})
        messages = []
        for message in result["messages"][:-1]: # 去除没有命中工具的AIMessage
            if not isinstance(message, HumanMessage) and not isinstance(message, SystemMessage):
                messages.append(message)
        return messages
        # 是否需要模型总结信息（增加10-20s的时间） ↓
        # return await self.conversation_model.ainvoke(result["messages"][:-1])
