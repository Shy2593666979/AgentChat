import asyncio
import copy
import time
from typing import Any, Dict, List

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware, wrap_tool_call
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command
from loguru import logger
from pydantic import BaseModel

from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.core.callbacks.usage_metadata import UsageMetadataCallbackHandler
from agentchat.core.models.manager import ModelManager
from agentchat.schemas.usage_stats import UsageStatsAgentType
from agentchat.services.mars.events import mars_tool_id
from agentchat.services.mars.mars_tools import MarsTool
from agentchat.services.mars.mars_tools.autobuild import construct_auto_build_prompt
from agentchat.utils.logging import tool_operation


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


    async def init_mars_agent(self):
        self.mars_tools = await self.setup_mars_tools()
        await self.setup_language_model()
        self.middlewares = await self.setup_middlewares()

        self.react_agent = self.setup_react_agent()

    async def setup_mars_tools(self) -> List[BaseTool]:
        mars_tools = []
        for name in MarsTool:
            if name == "auto_build_agent":
                auto_build_prompt = await construct_auto_build_prompt(self.mars_config.user_id)
                mars_tool = copy.deepcopy(MarsTool[name])
                mars_tool.description = mars_tool.description.replace("{{{user_configs_placeholder}}}", auto_build_prompt)
                mars_tools.append(mars_tool)
            else:
                mars_tools.append(MarsTool[name])
        return mars_tools

    async def setup_language_model(self):
        # 普通对话模型
        self.chat_model = ModelManager.get_chat_model()

        # 支持Function Call模型
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()

        # 推理模型
        self.reasoning_model = ModelManager.get_reasoning_model()

    def setup_react_agent(self):
        return create_agent(
            model=self.chat_model,
            tools=self.mars_tools,
            middleware=self.middlewares,
        )

    async def setup_middlewares(self):
        tool_call_limiter = ToolCallLimitMiddleware(
            thread_limit=8
        )

        @wrap_tool_call
        async def handler_tool_call(
            request: ToolCallRequest,
            handler,
        ) -> ToolMessage | Command:
            request.tool_call["args"].update(
                {
                    "user_id": self.mars_config.user_id,
                }
            )
            name = request.tool_call["name"]
            labels = {
                "auto_build_agent": "构建智能体",
                "deep_search": "深度搜索",
                "crawl_ai_news": "生成 AI 日报",
                "query_knowledge": "检索知识库",
            }
            started = time.monotonic()
            icons = {
                "auto_build_agent": "bot",
                "deep_search": "search",
                "crawl_ai_news": "file",
                "query_knowledge": "book",
            }
            data = {
                "id": request.tool_call["id"],
                "name": name,
                "label": labels.get(name, name),
                "icon": icons.get(name, "tool"),
            }
            self.is_call_tool = True
            self.reasoning_interrupt.set()
            await self.mars_output_queue.put(
                {
                    "type": "tool_start",
                    "time": time.time(),
                    "data": data,
                }
            )
            context_token = mars_tool_id.set(request.tool_call["id"])
            try:
                with tool_operation("mars.tool", tool=name, tool_call_id=request.tool_call["id"]) as operation:
                    tool_result = await handler(request)
                    operation["failed"] = getattr(tool_result, "status", None) == "error"
            except Exception:
                await self.mars_output_queue.put(
                    {
                        "type": "tool_error",
                        "time": time.time(),
                        "data": {
                            **data,
                            "elapsed": round(time.monotonic() - started, 1),
                        },
                    }
                )
                raise
            finally:
                mars_tool_id.reset(context_token)
            failed = isinstance(tool_result, ToolMessage) and tool_result.status == "error"
            await self.mars_output_queue.put(
                {
                    "type": "tool_error" if failed else "tool_end",
                    "time": time.time(),
                    "data": {
                        **data,
                        "elapsed": round(time.monotonic() - started, 1),
                    },
                }
            )
            if isinstance(tool_result, (ToolMessage, Command)):
                return tool_result
            return ToolMessage(content=tool_result, name=request.tool_call["name"], tool_call_id=request.tool_call["id"])

        return [tool_call_limiter, handler_tool_call]


    async def ainvoke_stream(self, messages: List[BaseMessage]):
        # 用于中断推理模型输出的事件
        self.reasoning_interrupt = asyncio.Event()
        # 用于存放Mars Agent输出的队列
        self.mars_output_queue = asyncio.Queue()

        self.is_call_tool = False

        callback = UsageMetadataCallbackHandler()
        async def run_mars_agent():
            """
            运行Mars Agent，执行工具调用并将其输出放入队列。
            """
            try:
                async for token, chunk in self.react_agent.astream(
                    input={
                        "messages": messages,
                    },
                    config={
                        "callbacks": [callback],
                    },
                    stream_mode=["custom"],
                ):
                    await self.mars_output_queue.put(chunk)
            except Exception:
                logger.exception("Mars 任务执行失败")
                await self.mars_output_queue.put(
                    {
                        "type": "error",
                        "data": {
                            "message": "任务执行失败，请检查模型或工具配置后重试。",
                        },
                    }
                )
            finally:
                await self.mars_output_queue.put(
                    {
                        "_producer_done": "agent",
                    }
                )

        async def run_reasoning_model():
            """
            运行推理模型，流式输出思考过程，并随时响应中断事件。
            """
            try:
                response = await self.reasoning_model.astream(messages)
                async for chunk in response:
                    # 在每次输出前检查是否需要中断
                    if self.reasoning_interrupt.is_set():
                        break

                    delta = chunk.choices[0].delta
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                        yield {
                            "type": "reasoning_chunk",
                            "time": time.time(),
                            "data": delta.reasoning_content,
                        }

                    if hasattr(delta, "content") and delta.content:
                        if self.is_call_tool: # 如果调用Mars工具的话 使用工具里面的信息进行回答
                            break
                        else:
                            yield {
                                "type": "response_chunk",
                                "source": "reasoning",
                                "time": time.time(),
                                "data": delta.content,
                            }
            except Exception as e:
                logger.error(f"推理模型流式输出错误: {e}")

        # --- 主执行流程 ---

        async def stream_reasoning():
            try:
                async for chunk in run_reasoning_model():
                    if not self.reasoning_interrupt.is_set():
                        await self.mars_output_queue.put(chunk)
            finally:
                await self.mars_output_queue.put(
                    {
                        "_producer_done": "reasoning",
                    }
                )

        # 两路输出共用队列，工具进度不再等待推理模型的首个响应。
        mars_task = asyncio.create_task(run_mars_agent())
        reasoning_task = asyncio.create_task(stream_reasoning())

        try:
            finished = set()
            while len(finished) < 2:
                mars_chunk = await self.mars_output_queue.get()
                if "_producer_done" in mars_chunk:
                    finished.add(mars_chunk["_producer_done"])
                    continue
                if mars_chunk.get("type") in ("tool_start", "error") and not reasoning_task.done():
                    self.reasoning_interrupt.set()
                    reasoning_task.cancel()
                yield mars_chunk
            await mars_task
        finally:
            # 客户端停止或断开时，同时取消后台执行，防止继续消耗模型调用。
            for pending in (mars_task, reasoning_task):
                if not pending.done():
                    pending.cancel()
            await asyncio.gather(mars_task, reasoning_task, return_exceptions=True)

    async def _record_agent_token_usage(self, response: AIMessage | AIMessageChunk | BaseMessage, model):
        if response.usage_metadata:
            await UsageStatsService.create_usage_stats(
                model=model,
                user_id=self.mars_config.user_id,
                agent=UsageStatsAgentType.mars_agent,
                input_tokens=response.usage_metadata.get("input_tokens"),
                output_tokens=response.usage_metadata.get("output_tokens")
            )
