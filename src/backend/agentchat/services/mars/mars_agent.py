import asyncio
import inspect
import json
import time
import typing
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage, SystemMessage, ToolCall, AIMessage, ToolMessage
from langchain_core.tools import Tool, BaseTool
from loguru import logger
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic import BaseModel, create_model, Field

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
                # TODO: 将chunk类型改成统一的response_chunk
                chunk["type"] = "response_chunk"
                yield chunk



    async def ainvoke_stream(self, messages: List[BaseMessage]):
        # 用于中断推理模型输出的事件
        reasoning_interrupt = asyncio.Event()
        # 用于存放Mars Agent输出的队列
        mars_output_queue = asyncio.Queue()


        async def run_mars_agent():
            """
            运行Mars Agent，执行工具调用并将其输出放入队列。
            """
            try:
                # 1. 判断是否需要调用工具
                call_tool_message = await self.call_tools_messages(messages)
                if not call_tool_message.tool_calls:
                    # 如果没有工具调用，放入None作为结束信号并直接返回
                    await mars_output_queue.put(None)
                    return

                messages.append(call_tool_message)

                # 2. 执行工具并处理输出
                first_chunk = True
                mars_task_first_chunk = {
                    "type": "response_chunk",
                    "time": time.time(),
                    "data": "#### 任务已经完成，我开始为你输出结果 ✅\n"
                }

                async for chunk in self.execute_tool_message(messages):
                    if first_chunk:
                        # 当第一个工具输出产生时，设置中断事件
                        reasoning_interrupt.set()
                        # 短暂等待，以确保推理任务有时间响应中断信号
                        await asyncio.sleep(0.01)
                        first_chunk = False
                        # 发送暂停推理，开始任务回复的信息
                        await mars_output_queue.put(mars_task_first_chunk)

                    # 将工具的输出块放入队列
                    await mars_output_queue.put(chunk)
                
                # 所有工具输出处理完毕，放入None作为结束信号
                await mars_output_queue.put(None)
            except Exception as e:
                logger.error(f"Mars Agent 执行出错: {e}")
                # 即使出错也要确保放入结束信号
                await mars_output_queue.put(None)

        async def run_reasoning_model():
            """
            运行推理模型，流式输出思考过程，并随时响应中断事件。
            """
            try:
                response = await self.reasoning_model.astream(messages)
                async for chunk in response:
                    # 在每次输出前检查是否需要中断
                    if reasoning_interrupt.is_set():
                        break

                    delta = chunk.choices[0].delta
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                        yield {
                            "type": "reasoning_chunk",
                            "time": time.time(),
                            "data": delta.reasoning_content
                        }

                    if hasattr(delta, "content") and delta.content:
                        yield {
                            "type": "response_chunk",
                            "time": time.time(),
                            "data": delta.content
                        }
            except Exception as e:
                logger.error(f"推理模型流式输出错误: {e}")

        # --- 主执行流程 ---

        # 1. 立即返回初始信息
        yield {
            "type": "response_chunk",
            "time": time.time(),
            "data": "#### 现在开始，我会边梳理思路边完成这项任务😊\n"
        }

        # 2. 在后台启动Mars Agent任务
        mars_task = asyncio.create_task(run_mars_agent())

        # 3. 首先，流式输出推理模型的思考过程，直到被中断
        async for reasoning_chunk in run_reasoning_model():
            yield reasoning_chunk

        # 4. 推理过程结束后，开始处理并输出Mars Agent的结果
        while True:
            mars_chunk = await mars_output_queue.get()
            if mars_chunk is None:  # 收到结束信号
                break
            yield mars_chunk

        # 5. 确保Mars Agent任务已彻底完成
        await mars_task



# 将OpenAI的function call格式转成Langchain格式做适配
def convert_langchain_tool_calls(tool_calls: List[ChatCompletionMessageToolCall]):
    langchain_tool_calls: List[ToolCall] = []

    for tool_call in tool_calls:
        langchain_tool_calls.append(
            ToolCall(id=tool_call.id, args=json.loads(tool_call.function.arguments), name=tool_call.function.name))

    return langchain_tool_calls




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
    sig = inspect.signature(func)
    fields = {
        name: (param.annotation, ... if param.default is inspect.Parameter.empty else param.default)
        for name, param in sig.parameters.items()
    }
    model = create_model(func.__name__, **fields)
    schema = model.model_json_schema()

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": schema
        },
    }


