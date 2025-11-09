import copy
import time
import asyncio

from loguru import logger
from pydantic.v1 import BaseModel
from typing import List, Dict, Any, AsyncGenerator, Optional, Callable, NotRequired

from langgraph.runtime import Runtime
from langgraph.types import Command
from langchain_core.tools import BaseTool, tool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents import create_agent, AgentState
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, ToolMessage, HumanMessage
from langchain.agents.middleware import LLMToolSelectorMiddleware, wrap_tool_call, ModelRequest, after_agent, \
    ModelResponse, AgentMiddleware

from agentchat.tools import AgentTools, AgentToolsWithName
from agentchat.api.services.llm import LLMService
from agentchat.core.models.manager import ModelManager
from agentchat.api.services.tool import ToolService
from agentchat.services.rag_handler import RagHandler
from agentchat.services.mcp_agent.agent import MCPAgent, MCPConfig
from agentchat.api.services.mcp_server import MCPService

class StreamAgentState(AgentState):
    tool_call_count: NotRequired[int]
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]



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
    def __init__(self, emit_event):
        super().__init__()
        self.emit_event = emit_event

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
        model_call_count = request.state.get("model_call_count", 0)
        select_tool_message = "开始选择可用工具" if model_call_count == 0 else f"是否需要继续调用工具{' ' * model_call_count}"
        # 发送工具分析开始事件
        await self.emit_event({
            "title": select_tool_message,
            "status": "START",
            "message": "正在分析需要使用的工具...",
        })

        response = await handler(request)
        if tool_calls := response.result[0].tool_calls:
            tool_call_names = [tool_call["name"] for tool_call in tool_calls]
            # 发送工具选择完成事件
            await self.emit_event({
                "title": select_tool_message,
                "status": "END",
                "message": "可用工具：" + ", ".join(set(tool_call_names))
            })

        await self.emit_event({
            "title": select_tool_message,
            "status": "END",
            "message": "无可使用的工具"
        })

        return response

    async def awrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        tool_call_count = request.state.get("tool_call_count", 0)
        # 发送工具分析开始事件
        await self.emit_event({
            "status": "START",
            "title": f"执行可用工具: {request.tool_call["name"]}",
            "message": f"正在调用插件工具 {request.tool_call["name"]}..."
        })
        request.state["tool_call_count"] = tool_call_count + 1

        tool_result = await handler(request)

        await self.emit_event(
            {
                "status": "END",
                "title": f"执行可用工具: {request.tool_call["name"]}",
                "message": tool_result.content
            }
        )
        return tool_result

class StreamingAgent:
    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config

        self.conversation_model = None
        self.tool_invocation_model = None
        self.react_agent = None

        self.tools = []
        self.mcp_agent_as_tools = []
        self.middlewares = []
        self.collection_names = []
        self.index_names = []

        # 流式事件队列
        self.event_queue = asyncio.Queue()
        self.stop_streaming = False

    async def emit_event(self, data: Dict[Any, Any]):
        """发送流式事件"""
        event = {
            "type": "event",
            "timestamp": time.time(),
            "data": data
        }
        await self.event_queue.put(event)

    async def init_agent(self):
        self.mcp_agent_as_tools = await self.setup_mcp_agent_as_tools()

        self.tools = await self.setup_tools()

        self.collection_names, self.index_names = await self.setup_knowledge_names()
        await self.setup_language_model()

        self.middlewares = await self.setup_agent_middleware()
        self.react_agent = self.setup_react_agent()

    async def setup_agent_middleware(self):
        tool_selector_middleware = LLMToolSelectorMiddleware(
            model=self.tool_invocation_model,
            max_tools=3 # 限制每次选择最多 3个工具
        )

        emit_event_middleware = EmitEventAgentMiddleware(
            self.emit_event
        )

        return [tool_selector_middleware, emit_event_middleware]


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
            middleware=self.middlewares,
            state_schema=StreamAgentState
        )


    async def setup_tools(self) -> List[BaseTool]:
        tools = []
        tools_name = await ToolService.get_tool_name_by_id(self.agent_config.tool_ids)
        for name in tools_name:
            tools.append(AgentToolsWithName.get(name))
        return tools

    async def setup_mcp_agent_as_tools(self):
        mcp_agent_as_tools = []


        def create_mcp_agent_as_tool(mcp_agent, mcp_as_tool_name, description):
            @tool(mcp_as_tool_name, description=description)
            async def call_mcp_agent(query: str):
                """
                用户想要根据这些mcp来完成的一些任务
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

            mcp_agent = MCPAgent(mcp_config, self.agent_config.user_id, self.emit_event)
            await mcp_agent.init_mcp_agent()

            mcp_agent_as_tools.append(create_mcp_agent_as_tool(mcp_agent, mcp_server.get("mcp_as_tool_name"), mcp_server.get("description")))

        return mcp_agent_as_tools

    async def setup_knowledge_names(self):
        return self.agent_config.knowledge_ids, self.agent_config.knowledge_ids


    async def call_knowledge_messages(self, messages: List[BaseMessage]) -> BaseMessage:
        """调用知识库，添加流式事件"""
        knowledge_query = messages[-1].content

        # 发送知识库检索开始事件
        await self.emit_event({
            "title": "检索知识库",
            "status":"START",
            "message": "开始执行知识库检索....",
        })

        # Milvus和ES检索相关的知识库
        knowledge_message = await RagHandler.retrieve_ranked_documents(
            knowledge_query, self.collection_names, self.index_names
        )

        # 发送知识库检索完成事件
        await self.emit_event({
            "title": "检索知识库",
            "message": knowledge_message[:500] + "..." if len(knowledge_message) > 500 else knowledge_message,
            "status": "END"
        })

        return SystemMessage(content=knowledge_message)


    async def ainvoke_streaming(self, messages: List[BaseMessage]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用主方法"""

        # 启动知识库检索
        knowledge_task = None
        if self.collection_names and len(self.collection_names) != 0:
            knowledge_task = asyncio.create_task(self.call_knowledge_messages(copy.deepcopy(messages)))

        # 启动ReAct Agent执行
        graph_task = None
        if self.tools or self.mcp_agent_as_tools:
            graph_task = asyncio.create_task(self.react_agent.ainvoke({"messages": messages, "model_call_count": 0, "user_id": self.agent_config.user_id}))

        # 收集所有任务
        all_tasks = [task for task in [knowledge_task, graph_task] if task is not None]

        # 流式返回事件
        conversation_ended = False

        while not conversation_ended:
            try:
                # 等待事件或超时
                event = await asyncio.wait_for(self.event_queue.get(), timeout=5.0)
                yield event

            except asyncio.TimeoutError:
                # 发送心跳事件
                yield {
                    "type": "heartbeat",
                    "timestamp": time.time(),
                    "data": {"message": "连接保持中..."}
                }

            # 检查任务执行是否完成
            if all(task.done() for task in all_tasks):
                conversation_ended = True

        # 等待知识库返回结果
        knowledge_message = knowledge_task.result() if knowledge_task and knowledge_task.done() else None

        # 等待ReAct Agent执行完成
        if graph_task and graph_task.done():
            results = graph_task.result()
            messages = results["messages"][:-1]  # 去除没有命中工具的message

        # 添加知识库消息并开始最终响应
        if knowledge_message:
            messages.append(knowledge_message)

        response_content = ""
        try:
            async for chunk in self.conversation_model.astream(messages):
                if self.stop_streaming:
                    break
                response_content += chunk.content
                yield {
                    "type": "response_chunk",
                    "timestamp": time.time(),
                    "data": {
                        "chunk": chunk.content,
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

    # 非流式版本（保持向后兼容）
    async def ainvoke(self, messages: List[BaseMessage]):
        """非流式版本（保持向后兼容）"""
        # 并发执行知识库检索、工具调用
        knowledge_task = None
        if self.collection_names and len(self.collection_names) != 0:
            knowledge_task = asyncio.create_task(self.call_knowledge_messages(copy.deepcopy(messages)))

        graph_task = None
        if self.tools and len(self.tools) != 0:
            graph_task = asyncio.create_task(self.react_agent.ainvoke({"messages": messages}))

        # 等待所有任务完成
        if knowledge_task:
            knowledge_message = await knowledge_task
        else:
            knowledge_message = None

        if graph_task:
            results = await graph_task
            messages = results["messages"][:-1]  # 去除没有命中工具的message
        else:
            messages = messages.copy()

        # 添加知识库消息
        if knowledge_message:
            messages.append(knowledge_message)

        # 收集完整响应
        response_content = ""
        async for chunk in self.conversation_model.astream(messages):
            response_content += chunk.content

        return response_content

    def stop_streaming_callback(self):
        self.stop_streaming = True

