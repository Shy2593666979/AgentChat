import asyncio
import inspect
import json
import time
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage, SystemMessage, ToolCall, AIMessage, ToolMessage
from langchain_core.tools import Tool, BaseTool
from loguru import logger
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic import BaseModel

from agentchat.core.models.manager import ModelManager
from agentchat.prompts.chat_prompt import DEFAULT_CALL_PROMPT
from agentchat.services.mars.mars_tools import Mars_Call_Tool
from agentchat.services.mars.mars_tools.autobuild import construct_auto_build_prompt
from agentchat.settings import app_settings


class MarsConfig(BaseModel):
    user_id: str

class MarsEnum:
    AutoBuild_Agent = 1
    Retrieval_Knowledge = 2
    AI_News = 3
    Deep_Search = 4



class MarsAgent:

    def __init__(self, mars_config: MarsConfig):
        self.mars_tools = None
        self.mars_config = mars_config

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

    async def init_mars_agent(self):

        self.mars_tools = await self.set_mars_tools()

        await self.set_language_model()
    # async def set_knowledges(self):
    #     pass
    #
    # async def set_mcp_agents(self):
    #     pass
    #
    # async def set_plugin_tools(self):
    #     pass

    async def set_mars_tools(self) -> List[BaseTool]:
        # TODO：因为Tool必须绑定func，但不用，加个test函数
        def test_func():
            pass

        mars_tools = []
        tools_name = [name for name, coroutine in Mars_Call_Tool.items()]
        for name in tools_name:
            mars_tools.append(Tool.from_function(name=name, description=Mars_Call_Tool[name].__doc__, func=test_func, coroutine=Mars_Call_Tool[name]))
        return mars_tools

    async def set_language_model(self):
        # 普通对话模型
        self.conversation_model = ModelManager.get_conversation_model()

        # 支持Function Call模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

        # 推理模型
        self.reasoning_model = ModelManager.get_reasoning_model()

    async def call_tools_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """调用工具选择，添加流式事件"""

        call_tool_messages: List[BaseMessage] = []

        # 只有一次工具调用
        tools_schema = []
        for tool in self.mars_tools:
            if tool.name == "auto_build_agent":
                auto_build_prompt = await construct_auto_build_prompt(self.mars_config.user_id)
                tool.coroutine.__doc__ = tool.coroutine.__doc__.replace("{{{user_configs_placeholder}}}", auto_build_prompt)
            tools_schema.append(function_to_args_schema(tool.coroutine))

        self.tool_invocation_model.bind_tools(tools_schema)

        system_message = SystemMessage(content=DEFAULT_CALL_PROMPT)
        call_tool_messages.append(system_message)

        call_tool_messages.extend(messages)

        response = await self.tool_invocation_model.ainvoke(call_tool_messages)
        # 判断是否有工具可调用
        if response.tool_calls:
            openai_tool_calls = response.tool_calls

            response.tool_calls = convert_langchain_tool_calls(response.tool_calls)


            return AIMessage(
                content=response.content,
                tool_calls=response.tool_calls,
            )
        else:
            return AIMessage(content="没有命中可用的工具")

    async def execute_tool_message(self, messages: List[BaseMessage]):
        """执行工具，添加流式事件"""
        tool_calls = messages[-1].tool_calls


        for tool_call in tool_calls:

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            use_tool = None
            for mars_tool in self.mars_tools:
                if mars_tool.name == tool_name:
                    use_tool = mars_tool

            # 更新用户参数到工具参数里面
            tool_args.update({"user_id": self.mars_config.user_id})

            async for chunk in use_tool.coroutine(**tool_args):
                yield chunk



    async def ainvoke_stream(self, messages: List[BaseMessage]):

        # await self.emit_event({
        #     "title": "开始模型推理",
        #     "status": "START",
        #     "message": "接下来我要认真分析用户的需求......"
        # })

        # 推理模型先行分析用户的需求

        reasoning_content = ""

        response = await self.reasoning_model.astream(messages)
        async for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                yield {
                    "type": "reasoning_chunk",
                    "time": time.time(),
                    "data": delta.reasoning_content
                }
                reasoning_content += delta.reasoning_content
            if hasattr(delta, "content") and delta.content:
                yield {
                    "type": "response_chunk",
                    "time": time.time(),
                    "data": delta.content
                }
        # async for chunk in self.reasoning_model.astream(messages):
        #     print(chunk)
        #     if chunk.content != "":
        #         yield {
        #             "type": "reasoning_chunk",
        #             "time": time.time(),
        #             "data": chunk.content
        #         }
        #         reasoning_content += chunk.content


        call_tool_message = await self.call_tools_messages(messages)

        messages.append(call_tool_message)

        async for chunk in self.execute_tool_message(messages):
            yield chunk




# 将OpenAI的function call格式转成Langchain格式做适配
def convert_langchain_tool_calls(tool_calls: List[ChatCompletionMessageToolCall]):
    langchain_tool_calls: List[ToolCall] = []

    for tool_call in tool_calls:
        langchain_tool_calls.append(
            ToolCall(id=tool_call.id, args=json.loads(tool_call.function.arguments), name=tool_call.function.name))

    return langchain_tool_calls


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


