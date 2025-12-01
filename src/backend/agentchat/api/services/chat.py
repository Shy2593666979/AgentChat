import copy
import time
import asyncio
from langchain.tools import ToolRuntime
from loguru import logger
from pydantic.v1 import BaseModel
from typing import List, Dict, Any, AsyncGenerator, Callable, NotRequired

from langgraph.runtime import Runtime
from langgraph.types import Command
from langchain_core.tools import BaseTool, tool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents import create_agent, AgentState
from langgraph.config import get_stream_writer
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, HumanMessage, AIMessageChunk
from langchain.agents.middleware import LLMToolSelectorMiddleware, ModelRequest, ModelResponse, AgentMiddleware

from agentchat.core.callbacks import usage_metadata_callback
from agentchat.tools import AgentToolsWithName
from agentchat.api.services.llm import LLMService
from agentchat.core.models.manager import ModelManager
from agentchat.api.services.tool import ToolService
from agentchat.services.rag_handler import RagHandler
from agentchat.core.agents.mcp_agent import MCPAgent, MCPConfig
from agentchat.api.services.mcp_server import MCPService

class StreamAgentState(AgentState):
    tool_call_count: NotRequired[int]
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]
    available_tools: NotRequired[List[BaseTool]]


MAX_TOOLS_SIZE = 10

class AgentConfig(BaseModel):
    mcp_ids: List[str]
    knowledge_ids: List[str]
    tool_ids: List[str]
    system_prompt: str
    enable_memory: bool = False
    name: str = None
    user_id: str
    llm_id: str


class EmitEventAgentMiddleware(AgentMiddleware):
    def __init__(self):
        super().__init__()

    async def aafter_model(
        self, state: StreamAgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return {
                "model_call_count": state["model_call_count"] + 1
            }

        return {
            "jump_to": "end"
        }

    async def awrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        try:
            if available_tools := request.state.get("available_tools", []):
                request.tools = available_tools
            response = await handler(request)
            return response
        except Exception as err:
            logger.error(f"Model call error: {err}")
            raise ValueError(err)

    async def awrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        writer = get_stream_writer()
        tool_call_count = request.state.get("tool_call_count", 0)
        # 发送工具分析开始事件
        writer({
            "status": "START",
            "title": f"执行可用工具: {request.tool_call["name"]}",
            "message": f"正在调用插件工具 {request.tool_call["name"]}..."
            })
        request.state["tool_call_count"] = tool_call_count + 1
        try:
            tool_result = await handler(request)
            writer({
                "status": "END",
                "title": f"执行可用工具: {request.tool_call["name"]}",
                "message": tool_result.content
                })
            return tool_result
        except Exception as err:
            writer({
                "status": "ERROR",
                "title": f"执行可用工具: {request.tool_call["name"]}",
                "message": str(err)
            })
            return ToolMessage(content=str(err), name=request.tool_call["name"], tool_call_id=request.tool_call["id"])

class StreamingAgent:
    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config

        self.conversation_model = None
        self.tool_invocation_model = None
        self.react_agent = None

        self.tools = []
        self.mcp_agent_as_tools = []
        self.middlewares = []

        # 流式事件队列
        self.event_queue = asyncio.Queue()
        self.stop_streaming = False

    def wrap_event(self, data: Dict[Any, Any]):
        """发送流式事件"""
        event = {
            "type": "event",
            "timestamp": time.time(),
            "data": data
        }
        return event

    async def init_agent(self):
        self.mcp_agent_as_tools = await self.setup_mcp_agent_as_tools()

        self.tools = await self.setup_tools()

        await self.setup_knowledge_tool()
        await self.setup_language_model()

        self.search_tool = self.setup_search_tool()
        self.middlewares = await self.setup_agent_middleware()
        self.react_agent = self.setup_react_agent()

    async def setup_agent_middleware(self):
        # 仅支持传入response_format为json object的模型
        tool_selector_middleware = LLMToolSelectorMiddleware(
            model=self.tool_invocation_model,
            max_tools=3 # 限制每次选择最多 3个工具
        )

        emit_event_middleware = EmitEventAgentMiddleware()

        return [emit_event_middleware]


    async def setup_language_model(self):
        # 普通对话模型
        if self.agent_config.llm_id:
            model_config = await LLMService.get_llm_by_id(self.agent_config.llm_id)
            self.conversation_model = ModelManager.get_user_model(**model_config)
        else:
            self.conversation_model = ModelManager.get_conversation_model()

        # 意图识别模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

    def setup_react_agent(self):
        return create_agent(
            model=self.conversation_model,
            tools=self.tools + self.mcp_agent_as_tools,
            #tools=[self.search_tool] if len(self.tools + self.mcp_agent_as_tools) >= MAX_TOOLS_SIZE else self.tools + self.mcp_agent_as_tools,
            middleware=self.middlewares,
            state_schema=StreamAgentState
        )

    def setup_search_tool(self):
        """这里相当于也是一个探索阶段，当绑定的工具数量很多时，会极大的占用上下文的Token数量以及影响命中效果
        所以在工具数量超过MaxToolsSize阈值后，会先只绑定一个搜索工具去搜索可用的工具，之后再拿着可用的工具进行对应的调用

        不适用：
            1.工具数量较少
            2.一些工具在每次对话都能用到
        """
        @tool(parse_docstring=True)
        def search_available_tools(query: str, tool_call_id):
            """
            搜索可用的工具，使用此工具查找是否包含相关的能力

            Args:
                query (str): 执行任务的关键词，例如 'github'、'search'、'天气'

            Returns:
                str: 返回本次任务可能能用到的接口
            """
            found_tools = []
            available_tools = self.tools + self.mcp_agent_as_tools
            for tool in available_tools:
                if tool.name == "search_available_tools":
                    continue
                if query.lower() in tool.name or query.lower() in tool.description:
                    found_tools.append(tool)

            if not found_tools:
                content_str = "未找到相关工具。请尝试其他关键词。"
            else:
                content_str = f"已找到并激活以下工具:\n" + "\n".join([tool.name for tool in found_tools]) + "\n\n现在你可以调用这些工具了。"

            tool_msg = ToolMessage(
                content=content_str,
                tool_call_id=tool_call_id,
                name="search_available_tools"
            )

            return Command(update={"available_tools": found_tools, "messages": [tool_msg]})
        return search_available_tools


    async def setup_tools(self) -> List[BaseTool]:
        tools = []
        tools_name = await ToolService.get_tool_name_by_id(self.agent_config.tool_ids)
        for name in tools_name:
            agent_tool = AgentToolsWithName.get(name)
            if agent_tool:
                tools.append(agent_tool)
        return tools

    async def setup_mcp_agent_as_tools(self):
        mcp_agent_as_tools = []


        def create_mcp_agent_as_tool(mcp_agent, mcp_as_tool_name, description):
            @tool(mcp_as_tool_name, description=description)
            async def call_mcp_agent(query: str):
                """
                用户想要根据这些mcp工具来完成的一些任务
                Args:
                    query: 用户询问的问题
                Returns:
                    根据该MCP Agent来完成的一些任务
                """

                messages = await mcp_agent.ainvoke([HumanMessage(content=query)])
                return "\n".join([message.content for message in messages])
            return call_mcp_agent

        for mcp_id in self.agent_config.mcp_ids:
            mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
            mcp_config = MCPConfig(**mcp_server)

            mcp_agent = MCPAgent(mcp_config, self.agent_config.user_id)
            await mcp_agent.init_mcp_agent()

            mcp_agent_as_tools.append(create_mcp_agent_as_tool(mcp_agent, mcp_server.get("mcp_as_tool_name"), mcp_server.get("description")))

        return mcp_agent_as_tools

    async def setup_knowledge_tool(self):
        @tool(parse_docstring=True)
        async def retrival_knowledge(query: str) -> str:
            """
            通过检索知识库来获取信息

            Args:
                query (str): 用户问题

            Returns:
                str: 返回从知识库检索来的信息
            """
            knowledge_message = await RagHandler.retrieve_ranked_documents(
                query, self.agent_config.knowledge_ids
            )
            return knowledge_message

        self.tools.append(retrival_knowledge)


    async def astream(self, messages: List[BaseMessage]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用主方法"""
        response_content = ""
        try:
            async for token, metadata in self.react_agent.astream(
                    input={"messages": copy.deepcopy(messages), "model_call_count": 0, "user_id": self.agent_config.user_id},
                    config={"callbacks": [usage_metadata_callback]},
                    stream_mode=["messages", "custom"],
            ):
                if token == "custom":
                    yield self.wrap_event(metadata)
                elif isinstance(metadata[0], AIMessageChunk) and metadata[0].content:
                    response_content += metadata[0].content
                    yield {
                        "type": "response_chunk",
                        "timestamp": time.time(),
                        "data": {
                            "chunk": metadata[0].content,
                            "accumulated": response_content
                        }
                    }

        # 针对模型回复进行兜底操作，错误类型包括：敏感词，模型问题
        except Exception as err:
            logger.error(f"LLM Model Error: {err}")
            yield {
                "type": "response_chunk",
                "timestamp": time.time(),
                "data": {
                    "chunk": "您的问题触及到我的知识盲区，请换个问题吧✨",
                    "accumulated": response_content
                }
            }

    def stop_streaming_callback(self):
        self.stop_streaming = True

