import asyncio
import copy
import json
import time
import inspect
from loguru import logger
from typing import List, Dict, Any, AsyncGenerator
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, ToolMessage, HumanMessage, ToolCall
from langchain_core.tools import BaseTool, Tool
from langgraph.graph import MessagesState, StateGraph, END, START
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic.v1 import BaseModel

from agentchat.api.services.llm import LLMService
from agentchat.core.models.manager import ModelManager
from agentchat.api.services.tool import ToolService
from agentchat.prompts.chat_prompt import DEFAULT_CALL_PROMPT
from agentchat.services.rag_handler import RagHandler
from agentchat.tools import Call_Tool
from agentchat.services.mcp.manager import MCPManager
from agentchat.services.mcp_agent.agent import MCPAgent, MCPConfig
from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.mcp_user_config import MCPUserConfigService


class AgentConfig(BaseModel):
    mcp_ids: List[str]
    knowledge_ids: List[str]
    tool_ids: List[str]
    system_prompt: str
    use_embedding: bool = False
    user_id: str
    llm_id: str


class StreamingAgent:
    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self.mcp_manager = MCPManager()
        self.conversation_model = None
        self.tool_invocation_model = None
        self.tools = []
        self.mcp_tools = []
        self.mcp_agents: List[MCPAgent] = []
        self.collection_names = []
        self.index_names = []
        self.graph = None

        # 流式事件队列
        self.event_queue = asyncio.Queue()
        self.step_counter_lock = asyncio.Lock()
        self.step_counter = 1

    async def emit_event(self, data: Dict[Any, Any]):
        """发送流式事件"""
        event = {
            "type": "event",
            "timestamp": time.time(),
            "data": data
        }
        await self.event_queue.put(event)

    async def init_agent(self):
        self.mcp_agents = await self.set_mcp_agents()

        self.tools = await self.set_tools()

        self.collection_names, self.index_names = await self.set_knowledge_names()
        await self.set_language_model()
        await self.set_agent_graph()

    async def set_language_model(self):
        # 普通对话模型
        if self.agent_config.llm_id:
            model_config = await LLMService.get_llm_by_id(self.agent_config.llm_id)
            self.conversation_model = ModelManager.get_user_model(**model_config)
        else:
            self.conversation_model = ModelManager.get_conversation_model()

        # 支持Function Call模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

    async def set_tools(self) -> List[BaseTool]:
        tools = []
        tools_name = await ToolService.get_tool_name_by_id(self.agent_config.tool_ids)
        for name in tools_name:
            tools.append(Tool(name=name, description=Call_Tool[name].__doc__, func=Call_Tool[name]))
        return tools

    async def set_mcp_agents(self) -> List[MCPAgent]:
        mcp_agents = []
        for mcp_id in self.agent_config.mcp_ids:
            mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
            mcp_config = MCPConfig(**mcp_server)

            mcp_agent = MCPAgent(mcp_config, self.agent_config.user_id)
            mcp_agents.append(mcp_agent)
        return mcp_agents

    async def set_knowledge_names(self):
        return self.agent_config.knowledge_ids, self.agent_config.knowledge_ids

    async def call_mcp_agent_messages(self, messages: List[BaseMessage]):

        async def process_mcp_agent(mcp_agent: MCPAgent):
            # 开始执行MCP Agent
            await self.emit_event({
                "status": "START",
                "title": f"Run MCP Agent: {mcp_agent.mcp_config.server_name}",
                "message": "开始执行MCP Agent...",
            })

            await mcp_agent.init_mcp_agent()

            responses = await mcp_agent.ainvoke(messages)

            # 返回MCP Agent结果
            await self.emit_event({
                "title": f"Run MCP Agent: {mcp_agent.mcp_config.server_name}",
                "message": "\n\n".join([response.content for response in responses]),
                "status": "END"
            })
            return responses

        process_tasks = [process_mcp_agent(mcp_agent) for mcp_agent in self.mcp_agents]
        results = await asyncio.gather(*process_tasks, return_exceptions=True)

        # # 并发初始化所有MCP Agent
        # init_tasks = [mcp_agent.init_mcp_agent() for mcp_agent in self.mcp_agents]
        # await asyncio.gather(*init_tasks)
        #
        # # 并发处理MCP Agent的循环流程
        # ainvoke_tasks = [asyncio.create_task(mcp_agent.ainvoke(messages)) for mcp_agent in self.mcp_agents]
        # results = asyncio.gather(*ainvoke_tasks, return_exceptions=True)

        # 获取MCP Agent信息并返回
        mcp_agent_messages: List[BaseMessage] = []
        for result in results:
            mcp_agent_messages.extend(result)
        return mcp_agent_messages

    async def call_tools_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """调用工具选择，添加流式事件"""

        # 发送工具分析开始事件
        await self.emit_event({
            "title": f"Run Select Tool_{self.step_counter}",
            "status": "START",
            "message": "正在分析需要使用的工具...",
        })

        call_tool_messages: List[BaseMessage] = []
        # 只有第一次调用工具的时候才会初始化
        if self.step_counter == 1:
            tools_schema = []
            for tool in self.tools:
                if isinstance(tool, BaseTool) and tool.args_schema:  # MCP Tool
                    tools_schema.append(mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema))
                else:
                    tools_schema.append(function_to_args_schema(tool.func))

            self.tool_invocation_model.bind_tools(tools_schema)

            system_message = SystemMessage(content=DEFAULT_CALL_PROMPT)
            call_tool_messages.append(system_message)

        call_tool_messages.extend(messages)

        response = await self.tool_invocation_model.ainvoke(call_tool_messages)
        # 判断是否有工具可调用
        if response.tool_calls:
            openai_tool_calls = response.tool_calls

            response.tool_calls = convert_langchain_tool_calls(response.tool_calls)
            # 发送工具选择完成事件
            await self.emit_event({
                "title": f"Run Select Tool_{self.step_counter}",
                "status": "END",
                "messages": ", ".join([tool_call["name"] for tool_call in response.tool_calls])
            })

            return AIMessage(
                content="命中可用工具",
                tool_calls=response.tool_calls,
            )
        else:
            # 发送无工具可用事件
            await self.emit_event({
                "title": f"Run Select Tool_{self.step_counter}",
                "status": "END",
                "message": "没有命中可用的工具"
            })
            return AIMessage(content="没有命中可用的工具")

    async def execute_tool_message(self, messages: List[ToolMessage]):
        """执行工具，添加流式事件"""
        tool_calls = messages[-1].tool_calls
        tool_messages: List[BaseMessage] = []

        # 保证不出现竞争条件
        async with self.step_counter_lock:
            self.step_counter += 1

        for tool_call in tool_calls:
            # 发送工具执行开始事件
            # await self.emit_event(f"Run Execution Tool: {tool_call["name"]}", {
            #     "status": "start",
            #     "step": self.step_counter,
            #     "tool_name": tool_call["name"],
            #     "tool_args": tool_call["args"],
            #     "tool_call_id": tool_call["id"]
            # })

            is_mcp_tool, use_tool = self.mcp_tool_use(tool_call["name"])
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            # TODO：去除对MCP 工具的单独调用，但保留
            if is_mcp_tool:
                try:
                    # 针对鉴权的MCP Server需要用户的单独配置，例如飞书、邮箱
                    mcp_server = await MCPService.get_server_from_tool_name(tool_name)
                    mcp_config = await MCPUserConfigService.get_mcp_user_config(self.agent_config.user_id,
                                                                                mcp_server["id"])
                    tool_args.update(mcp_config)

                    # 发送MCP工具调用事件
                    await self.emit_event({
                        "status": "START",
                        "title": f"Run MCP Tool: {tool_name}",
                        "message": f"正在调用MCP工具 {tool_name}..."
                    })

                    # 调用MCP 工具返回结果
                    tool_result = await use_tool.coroutine(**tool_args)

                    # 发送MCP工具执行完成事件
                    await self.emit_event({
                        "status": "END",
                        "title": f"Run MCP Tool: {tool_name}",
                        "message": tool_result,
                    })

                    tool_messages.append(
                        ToolMessage(content=tool_result, name=tool_name + "_mcp", tool_call_id=tool_call_id))
                    logger.info(f"MCP Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")

                except Exception as err:
                    # 发送MCP工具执行错误事件
                    await self.emit_event({
                        "status": "ERROR",
                        "message": str(err),
                        "title": f"Run MCP Tool: {tool_name}",
                    })

                    logger.error(f"MCP Tool {tool_name} Error: {str(err)}")
                    tool_messages.append(
                        ToolMessage(content=str(err), name=tool_name + "_mcp", tool_call_id=tool_call_id))
            else:
                try:
                    # 发送插件工具调用事件
                    await self.emit_event({
                        "status": "START",
                        "title": f"Run Execution Tool: {tool_name}",
                        "message": f"正在调用插件工具 {tool_name}..."
                    })

                    tool_result = use_tool.func(**tool_args)

                    # 发送插件工具执行完成事件
                    await self.emit_event({
                        "status": "END",
                        "title": f"Run Execution Tool: {tool_name}",
                        "message": tool_result,
                    })

                    tool_messages.append(
                        ToolMessage(content=tool_result, name=tool_name, tool_call_id=tool_call_id))
                    logger.info(f"Plugin Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")

                except Exception as err:
                    # 发送插件工具执行错误事件
                    await self.emit_event({
                        "status": "ERROR",
                        "title": f"Run Execution Tool: {tool_name}",
                        "message": str(err),
                    })

                    logger.error(f"Plugin Tool {tool_name} Error: {str(err)}")
                    tool_messages.append(
                        ToolMessage(content=str(err), name=tool_name, tool_call_id=tool_call_id))

        return tool_messages

    async def call_knowledge_messages(self, messages: List[BaseMessage]) -> BaseMessage:
        """调用知识库，添加流式事件"""
        knowledge_query = messages[-1].content

        # 发送知识库检索开始事件
        await self.emit_event({
            "title": "Run Retrieval Knowledge",
            "status":"START",
            "message": "开始执行知识库检索....",
        })

        # Milvus和ES检索相关的知识库
        knowledge_message = await RagHandler.retrieve_ranked_documents(
            knowledge_query, self.collection_names, self.index_names
        )

        # 发送知识库检索完成事件
        await self.emit_event({
            "title": "Run Retrieval Knowledge",
            "message": knowledge_message[:500] + "..." if len(knowledge_message) > 500 else knowledge_message,
            "status": "END"
        })

        return SystemMessage(content=knowledge_message)

    async def set_agent_graph(self):
        """设置Agent图，添加流式事件支持"""

        # 构建调用工具Graph
        async def should_continue(state: MessagesState):
            messages = state["messages"]
            last_message = messages[-1]

            # 如果工具递归调用次数超过5次，直接返回END
            if self.step_counter > 5:
                return END

            if last_message.tool_calls:
                # 发送继续执行工具事件
                # await self.emit_event("continue_tool_execution", {
                #     "message": "检测到工具调用，继续执行...",
                #     "tool_calls_count": len(last_message.tool_calls)
                # })
                return "execute_tool_node"
            else:
                # 发送工具执行完成事件
                # await self.emit_event("tool_execution_finished", {
                #     "message": "所有工具执行完成，准备生成最终回答"
                # })
                return END

        async def call_tool_node(state: MessagesState):
            messages = state["messages"]

            # 发送工具选择节点开始事件
            # await self.emit_event("tool_selection_node_start", {
            #     "message": "进入工具选择节点"
            # })

            tool_message = await self.call_tools_messages(messages)
            messages.append(tool_message)

            return {"messages": messages}

        async def execute_tool_node(state: MessagesState):
            messages = state["messages"]

            # 发送工具执行节点开始事件
            # await self.emit_event("tool_execution_node_start", {
            #     "message": "进入工具执行节点"
            # })

            tool_results = await self.execute_tool_message(messages)
            messages.extend(tool_results)

            return {"messages": messages}

        workflow = StateGraph(MessagesState)

        workflow.add_node("call_tool_node", call_tool_node)
        workflow.add_node("execute_tool_node", execute_tool_node)

        # 设置起始节点
        workflow.add_edge(START, "call_tool_node")
        # 设置判断是否调用工具边
        workflow.add_conditional_edges("call_tool_node", should_continue)
        # 检测是否存在工具递归信息
        workflow.add_edge("execute_tool_node", "call_tool_node")

        self.graph = workflow.compile()

    async def ainvoke_streaming(self, messages: List[BaseMessage]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用主方法"""

        # 发送开始事件
        # await self.emit_event("conversation_start", {
        #     "user_message": messages[-1].content,
        #     "message": "开始处理您的请求..."
        # })

        # 启动知识库检索
        knowledge_task = None
        if self.collection_names and len(self.collection_names) != 0:
            knowledge_task = asyncio.create_task(self.call_knowledge_messages(copy.deepcopy(messages)))


        # 启动MCP Agent执行
        mcp_agent_task = None
        if self.mcp_agents and len(self.mcp_agents) != 0:
            mcp_agent_task = asyncio.create_task(self.call_mcp_agent_messages(copy.deepcopy(messages)))

        # 启动图执行
        graph_task = None
        if self.tools and len(self.tools) != 0:
            graph_task = asyncio.create_task(self.graph.ainvoke({"messages": messages}))

        # 收集所有任务
        all_tasks = [task for task in [knowledge_task, mcp_agent_task, graph_task] if task is not None]

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

        # 等待MCP Agent任务返回
        mcp_agent_messages = mcp_agent_task.result() if mcp_agent_task and mcp_agent_task.done() else None

        # 等待图执行完成
        if graph_task and graph_task.done():
            results = graph_task.result()
            messages = results["messages"][:-1]  # 去除没有命中工具的message

        # 添加MCP Agent消息
        if mcp_agent_messages:
            messages.extend(mcp_agent_messages)

        # 添加知识库消息并开始最终响应
        if knowledge_message:
            messages.append(knowledge_message)

        # 将HumanMessage移到最后
        idx = next((i for i in reversed(range(len(messages))) if isinstance(messages[i], HumanMessage)), -1)
        messages = messages[:idx] + messages[idx + 1:] + [messages[idx]] if idx != -1 and idx != len(messages) - 1 else messages
        
        
        response_content = ""
        try:
            async for chunk in self.conversation_model.astream(messages):
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
        # 并发执行知识库检索、MCP Agent和工具调用
        knowledge_task = None
        if self.collection_names and len(self.collection_names) != 0:
            knowledge_task = asyncio.create_task(self.call_knowledge_messages(copy.deepcopy(messages)))

        mcp_agent_task = None
        if self.mcp_agents and len(self.mcp_agents) != 0:
            mcp_agent_task = asyncio.create_task(self.call_mcp_agent_messages(copy.deepcopy(messages)))

        graph_task = None
        if self.tools and len(self.tools) != 0:
            graph_task = asyncio.create_task(self.graph.ainvoke({"messages": messages}))

        # 等待所有任务完成
        if knowledge_task:
            knowledge_message = await knowledge_task
        else:
            knowledge_message = None

        if mcp_agent_task:
            mcp_agent_messages = await mcp_agent_task
        else:
            mcp_agent_messages = None

        if graph_task:
            results = await graph_task
            messages = results["messages"][:-1]  # 去除没有命中工具的message
        else:
            messages = messages.copy()

        # 添加MCP Agent消息
        if mcp_agent_messages:
            messages.extend(mcp_agent_messages)

        # 添加知识库消息
        if knowledge_message:
            messages.append(knowledge_message)

        # 将HumanMessage移到最后
        idx = next((i for i in reversed(range(len(messages))) if isinstance(messages[i], HumanMessage)), -1)
        messages = messages[:idx] + messages[idx + 1:] + [messages[idx]] if idx != -1 and idx != len(
            messages) - 1 else messages

        # 收集完整响应
        response_content = ""
        async for chunk in self.conversation_model.astream(messages):
            response_content += chunk.content

        return response_content

    # 新增辅助方法
    def mcp_tool_use(self, tool_name: str):
        """判断是否为MCP工具并返回对应的工具实例"""
        for tool in self.tools:
            if tool.name == tool_name and tool in self.mcp_tools:
                return True, tool
            elif tool.name == tool_name:
                return False, tool
        return False, None


# 将OpenAI的function call格式转成Langchain格式做适配
def convert_langchain_tool_calls(tool_calls: List[ChatCompletionMessageToolCall]):
    langchain_tool_calls: List[ToolCall] = []

    for tool_call in tool_calls:
        langchain_tool_calls.append(
            ToolCall(id=tool_call.id, args=json.loads(tool_call.function.arguments), name=tool_call.function.name))

    return langchain_tool_calls


# 将Langchain的格式转为OpenAI的格式适配
def convert_openai_tool_calls(tool_calls: List[ToolCall]):
    openai_tool_calls: List[ChatCompletionMessageToolCall] = []

    for tool_call in tool_calls:
        openai_tool_calls.append(ChatCompletionMessageToolCall(id=tool_call.id, type="function",
                                                               function=Function(arguments=tool_call.args,
                                                                                 name=tool_call.name)))

    return openai_tool_calls


def mcp_tool_to_args_schema(name, description, args_schema) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": args_schema
        }
    }


# 将函数转成function schema格式
def function_to_args_schema(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown schema annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"schema": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }

# ❌ AgentChat V1.0 版本❌
# class ChatAgent:
#     def __init__(self, agent_config: AgentConfig):
#         self.agent_config = agent_config
#         self.mcp_manager = MCPManager(timeout=10)
#
#
#     async def init_agent(self):
#         self.tools = await self.set_tools()
#         self.mcp_tools = await self.set_mcp_tools()
#         self.tools.extend(self.mcp_tools)
#
#         self.collection_names, self.index_names = await self.set_knowledge_names()
#         await self.set_language_model()
#         await self.set_agent_graph()
#
#     async def set_language_model(self):
#         # 普通对话模型
#         if self.agent_config.llm_id:
#             model_config = await LLMService.get_llm_by_id(self.agent_config.llm_id)
#             self.conversation_model = ModelManager.get_user_model(**model_config)
#         else:
#             self.conversation_model = ModelManager.get_conversation_model()
#
#         # 支持Function Call模型
#         self.tool_invocation_model = ModelManager.get_tool_invocation_model()
#
#         # 推理模型
#         # self.reasoning_model = ModelManager.get_reasoning_model()
#
#     async def set_mcp_tools(self) -> List[BaseTool]:
#         mcp_tools = await self.mcp_manager.get_mcp_tools()
#         return mcp_tools
#
#     async def set_tools(self) -> List[BaseTool]:
#         tools = []
#         tools_name = await ToolService.get_tool_name_by_id(self.agent_config.tool_ids)
#         for name in tools_name:
#             tools.append(Tool(name=name, description=Call_Tool[name].__doc__, func=Call_Tool[name]))
#         return tools
#
#     async def set_knowledge_names(self):
#         return self.agent_config.knowledge_ids, self.agent_config.knowledge_ids
#
#     async def call_tools_messages(self, messages: List[BaseMessage]) -> BaseMessage:
#         for tool in self.tools:
#             if isinstance(tool, BaseTool) and tool.args_schema:
#                 tool.args_schema = function_to_args_schema(tool.func)
#
#         self.tool_invocation_model.bind_tools(self.tools)
#
#         system_message = SystemMessage(content=DEFAULT_CALL_PROMPT)
#         call_tool_messages = [system_message, messages[-1]]
#
#         response = await self.tool_invocation_model.ainvoke(call_tool_messages)
#         if response.additional_kwargs:
#             return AIMessage(
#                 content="",
#                 additional_kwargs=response.additional_kwargs,
#                 usage_metadata=response.usage_metadata,
#                 tool_calls=response.tool_calls,
#                 id=response.id,
#                 response_metadata=response.response_metadata
#             )
#         else:
#             return AIMessage(content="没有命中可用的工具")
#
#     async def execute_tool_message(self, messages: List[BaseMessage]):
#         tool_calls = messages[-1].tool_calls
#         tool_messages: List[BaseMessage] = []
#         for tool_call in tool_calls:
#             is_mcp_tool, use_tool = self.mcp_tool_use(tool_call["name"])
#             tool_name = tool_call["name"]
#             tool_args = tool_call["args"]
#             tool_call_id = tool_call["id"]
#             if is_mcp_tool:
#                 try:
#                     # 针对鉴权的MCP Server需要用户的单独配置，例如飞书、邮箱
#                     mcp_server = await MCPService.get_server_from_tool_name(tool_name)
#                     mcp_config = await MCPUserConfigService.get_mcp_user_config(self.agent_config.user_id, mcp_server["id"])
#                     tool_args.update(mcp_config)
#                     # 调用MCP 工具返回结果
#                     tool_result = await use_tool.coroutine(tool_name, tool_args)
#                     tool_messages.append(
#                         ToolMessage(content=tool_result, name=tool_name + "_mcp", tool_call_id=tool_call_id))
#                     logger.info(f"MCP Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")
#                 except Exception as err:
#                     logger.error(f"MCP Tool {tool_name} Error: {str(err)}")
#                     tool_messages.append(
#                         ToolMessage(content=str(err), name=tool_name + "_mcp", tool_call_id=tool_call_id))
#             else:
#                 try:
#                     tool_result = use_tool.func(tool_args)
#                     tool_messages.append(
#                         ToolMessage(content=tool_result, name=tool_name, tool_call_id=tool_call_id))
#                     logger.info(f"Plugin Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")
#                 except Exception as err:
#                     logger.error(f"Plugin Tool {tool_name} Error: {str(err)}")
#                     tool_messages.append(
#                         ToolMessage(content=str(err), name=tool_name, tool_call_id=tool_call_id))
#         return tool_messages
#
#
#     async def call_knowledge_messages(self, messages: List[BaseMessage]) -> BaseMessage:
#         knowledge_query = messages[-1].content
#
#         # Milvus和ES检索相关的知识库
#         knowledge_message = await RagHandler.retrieve_ranked_documents(knowledge_query, self.collection_names, self.index_names)
#         return SystemMessage(content=knowledge_message)
#
#
#     async def ainvoke(self, messages: List[BaseMessage]):
#         knowledge_message = await self.call_knowledge_messages(copy.deepcopy(messages))
#
#         await self.graph.ainvoke({"messages": messages})
#         messages.append(knowledge_message)
#
#         async for chunk in self.conversation_model.astream(messages):
#             yield chunk.content
#
#     async def set_agent_graph(self):
#
#         # 构建调用工具Graph
#         async def should_continue(state: MessagesState):
#             messages = state["messages"]
#             last_message = messages[-1]
#
#             if last_message.tool_calls:
#                 return "execute_tool_node"
#             else:
#                 return END
#
#         async def call_tool_node(state: MessagesState):
#             messages = state["messages"]
#             tool_message = await self.call_tools_messages(messages)
#             messages.extend(tool_message)
#
#             return {"messages": messages}
#
#         async def execute_tool_node(state: MessagesState):
#             messages = state["messages"]
#             tool_results = await self.execute_tool_message(messages)
#             messages.extend(tool_results)
#
#             return {"messages": messages}
#
#         workflow = StateGraph(MessagesState)
#
#         workflow.add_node("call_tool_node", call_tool_node)
#         workflow.add_node("execute_tool_node", execute_tool_node)
#
#         # 设置起始节点
#         workflow.add_edge(START, "call_tool_node")
#         # 设置判断是否调用工具边
#         workflow.add_conditional_edges("call_tool_node", should_continue)
#         # 检测是否存在工具递归信息
#         workflow.add_edge("execute_tool_node", "call_tool_node")
#
#         self.graph = workflow.compile()
#
#
#     async def connect_mcp_server(self):
#         servers = []
#         for mcp_id in self.agent_config.mcp_ids:
#             server = await MCPService.get_mcp_server_from_id(mcp_id)
#             servers.append(server)
#
#         await self.mcp_manager.connect_mcp_servers(servers)
#
#     def mcp_tool_use(self, tool_name):
#         for tool in self.tools:
#             if tool.name == tool_name and tool in self.mcp_tools:
#                 return True, tool
#             elif tool.name == tool_name:
#                 return False, tool
#         return False, None
#
#

# ❌ V0.1版本 ❌
# class ChatService:
#     def __init__(self, **kwargs):
#         self.llm_id = kwargs.get('llm_id')
#         self.tools_id = kwargs.get('tool_id')
#         self.dialog_id = kwargs.get('dialog_id')
#         self.mcp_ids = kwargs.get("mcp_ids")
#         self.embedding_id = kwargs.get('embedding_id')
#         self.knowledges_id = kwargs.get('knowledge_id')
#         self.mcp_manager = MCPManager(timeout=10)
#         self.llm_call = None
#         self.mcp_tools = None
#         self.llm = None
#         self.embedding = None
#         self.tools = []
#
#
#     async def init_agent(self):
#         await self.init_mcp()
#         await self.setup_llm()
#         await self.setup_tools()
#         await self.setup_mcp_tools()
#
#     async def setup_llm(self):
#         llm_config = LLMService.get_llm_by_id(llm_id=self.llm_id)
#         self.llm = ChatOpenAI(model=llm_config.model,
#                               base_url=llm_config.base_url, api_key=llm_config.api_key)
#
#         self.llm_call = FUNCTION_CALL_MSG if llm_config.model in Function_Call_provider else REACT_MSG
#         # Agent支持Embedding后初始化
#         if self.embedding_id:
#             await self.init_embedding()
#
#     async def init_embedding(self):
#
#         embedding_config = LLMService.get_llm_by_id(llm_id=self.embedding_id)
#         self.embedding = OpenAIEmbeddings(model=embedding_config.model,
#                                           base_url=embedding_config.base_url, api_key=embedding_config.api_key)
#
#     async def init_mcp(self):
#         servers = []
#         for mcp_id in self.mcp_ids:
#             server = MCPServerService.get_mcp_server_user(mcp_id)
#             servers.append(server)
#
#         await self.mcp_manager.connect_mcp_servers(servers)
#
#     async def setup_mcp_tools(self):
#         mcp_tools = await self.mcp_manager.get_mcp_tools()
#         self.mcp_tools = mcp_tools
#
#     async def setup_tools(self):
#         tools_name = ToolService.get_tool_name_by_id(self.tools_id)
#         if self.llm_call == REACT_MSG:
#             for name in tools_name:
#                 func = action_React[name]
#                 self.tools.append(ChatService.function_to_json(func))
#         else:
#              for name in tools_name:
#                 self.tools.append(action_Function_call[name])
#
#
#     async def run(self, messages: List[BaseMessage]):
#
#         user_input = messages[-1].content
#         # 都是通过检索RAG，并发可以减少消耗时间
#         history_messages, recall_knowledge_data = await asyncio.gather(
#             self.get_history_message(user_input=user_input, dialog_id=self.dialog_id),
#             RagHandler.rag_query(user_input, self.knowledges_id)
#         )
#
#         messages.extend(history_messages)
#         # history_message = await self.get_history_message(user_input=user_input, dialog_id=self.dialog_id)
#         # recall_knowledge_data = await RagHandler.rag_query(user_input, self.knowledges_id)
#
#         if self.llm_call == 'React':
#             return self._run_react(messages, recall_knowledge_data)
#         else:
#             return self._run_function_call(messages, recall_knowledge_data)
#
#     async def _run_react(self, messages: List[BaseMessage], recall_knowledge_data: str):
#         agent = create_structured_chat_agent(llm=self.llm, tools=self.tools)
#         agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
#         messages.append(AIMessage(content=recall_knowledge_data))
#
#         async for chunk in agent_executor.astream(messages):
#             yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)
#
#     async def _run_function_call(self, user_input: str, history_message: str, recall_knowledge_text: str):
#
#         # 并发执行不同类型的工具
#         tools_result, mcp_tools_result = asyncio.gather(
#             self.call_common_tool(user_input, history_message),
#             self.call_mcp_tool(user_input, history_message)
#         )
#
#
#         prompt_template = PromptTemplate.from_template(function_call_prompt)
#
#         chain = prompt_template | self.llm
#         async for chunk in chain.astream({'input': user_input, 'history': history_message, 'tools_result': tools_result, "mcp_tools_result": mcp_tools_result, "knowledge_result": recall_knowledge_text}):
#             yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)
#
#     async def call_common_tool(self, user_input, history_message):
#         # 普通的插件调用
#         func_prompt = function_call_template.format(input=user_input, history=history_message)
#         fun_name, args = await self._function_call(user_input=func_prompt)
#         tools_result = self.exec_tools(fun_name, args)
#         return tools_result
#
#     async def call_mcp_tool(self, user_input, history_message):
#         # MCP 插件调用
#         mcp_tool_prompt = function_call_template.format(input=user_input, history=history_message)
#         mcp_tool_name, mcp_tool_args = await self._mcp_function_call(user_input=mcp_tool_prompt)
#         mcp_tool_result = self.exec_mcp_tools(mcp_tool_name, mcp_tool_args)
#         return mcp_tool_result
#
#     async def _function_call(self, user_input: str):
#         messages = [HumanMessage(content=user_input)]
#         message = self.llm.invoke(
#             messages,
#             functions=self.tools,
#         )
#         try:
#             if message.additional_kwargs:
#                 function_name = message.additional_kwargs["function_call"]["name"]
#                 arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])
#
#                 logger.info(f"Function call result: \n function_name: {function_name} \n arguments: {arguments}")
#                 return function_name, arguments
#             else:
#                 raise ValueError
#         except Exception as err:
#             logger.info(f"Function call is not appear: {err}")
#             return None, None
#
#     async def _mcp_function_call(self, user_input: str):
#         messages = [HumanMessage(content=user_input)]
#         message = self.llm.invoke(
#             messages,
#             functions=self.mcp_tools,
#         )
#         try:
#             if message.additional_kwargs:
#                 function_name = message.additional_kwargs["function_call"]["name"]
#                 arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])
#
#                 logger.info(f"Function call result: \n function_name: {function_name} \n arguments: {arguments}")
#                 return function_name, arguments
#             else:
#                 raise ValueError
#         except Exception as err:
#             logger.info(f"Function call is not appear: {err}")
#             return None, None
#
#     async def exec_mcp_tools(self, mcp_tool_name, mcp_tool_args):
#         mcp_tools_info = {
#             "tool_name": mcp_tool_name,
#             "tool_args": mcp_tool_args
#         }
#         mcp_tool_results = self.mcp_manager.call_mcp_tools([mcp_tools_info])
#         return mcp_tool_results
#
#     async def exec_tools(self, func_name, args):
#         try:
#             action = action_Function_call[func_name]
#             result = action(**args)
#             return result
#         except Exception as err:
#             logger.error(f"action appear error: {err}")
#             return fail_action_prompt
#
#
#     async def get_history_message(self, user_input: str, dialog_id: str, top_k: int = 5) -> List[BaseMessage]:
#         # 如果绑定了Embedding模型，默认走RAG检索聊天记录
#         if self.embedding:
#             messages = await self._retrieval_history(user_input, dialog_id, top_k)
#             return messages
#         else:
#             messages = await self._direct_history(dialog_id, top_k)
#             return messages
#
#     @staticmethod
#     async def _direct_history(dialog_id: str, top_k: int):
#         messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k)
#         results = []
#         # for message in enumerate(messages):
#         #     if idx % 2 == 0:
#         #         results.append(HumanMessage(content=message.content))
#         #     else:
#         #         results.append(AIMessage(content=message.content))
#         return results
#
#     # 使用RAG检索的方式将最近2 * top_k条数据按照相关性排序，取其中top_k个
#     async def _retrieval_history(self, user_input: str, dialog_id: str, top_k: int):
#
#         # messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k * 2)
#         #
#         # for msg in messages:
#         #     self.collection.add(documents=[msg.to_str()], ids=[uuid4().hex])
#         #
#         # results = self.collection.query(query_texts=[user_input], n_results=top_k)
#         # history = ''.join(results['documents'][0])
#         # return history
#         messages = await RagHandler.rag_query(user_input, dialog_id, 0.6, top_k, False)
#         return [SystemMessage(content=messages)]
#
