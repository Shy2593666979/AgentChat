import asyncio
import inspect
import json
from typing import List

from langchain_core.messages import ToolMessage, BaseMessage, AIMessage, SystemMessage, ToolCall, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from loguru import logger
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic import BaseModel

from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.chat import DEFAULT_CALL_PROMPT
from agentchat.services.mcp.manager import MCPManager
from agentchat.utils.helpers import fix_json_text


class MCPConfig(BaseModel):
    url: str
    type: str = "sse"
    tools: List[str] = []
    server_name: str
    mcp_server_id: str


class MCPAgent:
    def __init__(self, mcp_config: MCPConfig, user_id: str):
        self.mcp_config = mcp_config
        self.mcp_manager = MCPManager()

        self.user_id = user_id
        self.mcp_tools: List[BaseTool] = []
        self.conversation_model = None
        self.tool_invocation_model = None
        self.graph = None
        self.step_counter = 0
        self.step_counter_lock = asyncio.Lock()

    async def init_mcp_agent(self):
        if self.mcp_config:
            await self.connect_mcp_server()
            self.mcp_tools = await self.set_mcp_tools()

        await self.set_language_model()
        await self.set_agent_graph()

    async def set_language_model(self):
        # 普通对话模型
        self.conversation_model = ModelManager.get_conversation_model()

        # 支持Function Call模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

    async def set_mcp_tools(self):
        mcp_tools = await self.mcp_manager.get_mcp_tools()
        return mcp_tools

    async def connect_mcp_server(self):
        server_info = {
            "url": self.mcp_config.url,
            "type": self.mcp_config.type,
            "server_name": self.mcp_config.server_name
        }
        await self.mcp_manager.connect_mcp_servers([server_info])

    async def call_tools_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """调用工具选择，添加流式事件"""

        call_tool_messages: List[BaseMessage] = []

        # 只有第一次调用工具的时候才会初始化
        if self.step_counter == 0:
            tools_schema = []
            for tool in self.mcp_tools:
                tools_schema.append(mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema))

            self.tool_invocation_model.bind_tools(tools_schema)

            system_message = SystemMessage(content=DEFAULT_CALL_PROMPT)
            # MCP Agent 单独的Prompt，不受历史记录影响
            call_tool_messages.append(system_message)
            call_tool_messages.append(messages[-1])
        else:
            call_tool_messages.extend(messages)

        response = await self.tool_invocation_model.ainvoke(call_tool_messages)
        # 判断是否有工具可调用
        if response.tool_calls:
            openai_tool_calls = response.tool_calls
            response.tool_calls = convert_langchain_tool_calls(response.tool_calls)

            return AIMessage(
                content="命中可用工具",
                tool_calls=response.tool_calls,
            )
        else:
            # 发送无工具可用事件
            return AIMessage(content="没有命中可用的工具")

    async def execute_tool_message(self, messages: List[ToolMessage]):
        """执行工具，添加流式事件"""
        tool_calls = messages[-1].tool_calls
        tool_messages: List[BaseMessage] = []

        for tool_call in tool_calls:
            # 保证不出现竞争条件
            async with self.step_counter_lock:
                self.step_counter += 1

            mcp_tool = self.find_mcp_tool(tool_call["name"])
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            try:
                # 针对鉴权的MCP Server需要用户的单独配置，例如飞书、邮箱
                mcp_config = await MCPUserConfigService.get_mcp_user_config(self.user_id,
                                                                            self.mcp_config.mcp_server_id)
                tool_args.update(mcp_config)

                # 调用MCP 工具返回结果
                tool_result = await mcp_tool.coroutine(**tool_args)

                tool_messages.append(
                    ToolMessage(content=tool_result, name=tool_name, tool_call_id=tool_call_id))
                logger.info(f"MCP Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")

            except Exception as err:
                # 发送MCP工具执行错误事件
                logger.error(f"MCP Tool {tool_name} Error: {str(err)}")
                tool_messages.append(
                    ToolMessage(content=str(err), name=tool_name, tool_call_id=tool_call_id))

        return tool_messages

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
                return "execute_tool_node"
            else:
                return END

        async def call_tool_node(state: MessagesState):
            messages = state["messages"]
            tool_message = await self.call_tools_messages(messages)
            messages.append(tool_message)

            return {"messages": messages}

        async def execute_tool_node(state: MessagesState):
            messages = state["messages"]

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

    async def ainvoke(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """非流式版本"""
        result = await self.graph.ainvoke({"messages": messages})
        messages = []
        for message in result["messages"][:-1]: # 去除没有命中工具的AIMessage
            if not isinstance(message, HumanMessage) and not isinstance(message, SystemMessage):
                messages.append(message)
        return messages
        # 是否需要模型总结信息（增加10-20s的时间） ↓
        # return await self.conversation_model.ainvoke(result["messages"][:-1])

    def find_mcp_tool(self, name) -> BaseTool | None:
        for tool in self.mcp_tools:
            if tool.name == name:
                return tool
        return None


# 将OpenAI的function call格式转成Langchain格式做适配
def convert_langchain_tool_calls(tool_calls: List[ChatCompletionMessageToolCall]):
    langchain_tool_calls: List[ToolCall] = []

    for tool_call in tool_calls:
        langchain_tool_calls.append(
            ToolCall(id=tool_call.id, args=json.loads(fix_json_text(tool_call.function.arguments)), name=tool_call.function.name))

    return langchain_tool_calls


# 将Langchain的格式转为OpenAI的格式适配
def convert_openai_tool_calls(self, tool_calls: List[ToolCall]):
    openai_tool_calls: List[ChatCompletionMessageToolCall] = []

    for tool_call in tool_calls:
        openai_tool_calls.append(ChatCompletionMessageToolCall(id=tool_call["id"], type="function",
                                                               function=Function(
                                                                   arguments=json.dumps(tool_call["args"]),
                                                                   name=tool_call["name"])))

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
