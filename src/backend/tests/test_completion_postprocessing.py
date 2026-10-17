"""真实响应结束不等待记忆服务，断开时仍保留已生成的历史。"""
import ast
import asyncio
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import List
from unittest.mock import AsyncMock

from fastapi import Depends, HTTPException, Request
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger
from starlette.background import BackgroundTask

from agentchat.api.responses.streaming import WatchedStreamingResponse
from agentchat.protocols.ag_ui import protocol_stream
from agentchat.schemas.completion import CompletionReq


class CompletionPostprocessingTests(unittest.IsolatedAsyncioTestCase):
    async def make_response(self, store_memory):
        class Agent:
            stop_streaming_callback = lambda self: None

            def __init__(self, config):
                pass

            async def init_agent(self):
                pass

            async def astream(self, messages):
                yield {"type": "response_chunk", "data": {"chunk": "回答"}}

        self.history = SimpleNamespace(
            get_short_term_messages=AsyncMock(return_value=[]),
            save_chat_history=AsyncMock(return_value={"first_user": False}),
        )
        self.conversation = SimpleNamespace(
            resolve_agent=AsyncMock(return_value={"id": "agent", "name": "测试", "system_prompt": "", "enable_memory": True}),
            get_conversation_history_summary=AsyncMock(return_value=""),
            update_conversation_summary=AsyncMock(),
        )
        ns = dict(globals(), ConversationService=self.conversation, HistoryService=self.history,
                  AgentConfig=lambda **values: SimpleNamespace(**values), GeneralAgent=Agent,
                  UserPayload=SimpleNamespace, get_login_user=lambda: None, memory_client=object(),
                  search_optional_memory=AsyncMock(return_value=("", True)), store_optional_memory=store_memory,
                  SYSTEM_PROMPT="test", attachment_events=lambda req: [], count_tokens_usage=lambda text: 1,
                  build_completion_user_input=lambda **values: values["user_input"],
                  build_completion_system_prompt=lambda *args: "test")
        for name in ("set_user_id_context", "set_agent_name_context", "set_conversation_id_context", "bind_log_context"):
            ns[name] = lambda *args, **kwargs: None
        path = Path(__file__).resolve().parents[1] / "agentchat/api/v1/completion.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        tree.body = [node for node in tree.body if getattr(node, "name", None) == "completion"]
        tree.body[0].decorator_list = []
        exec(compile(tree, str(path), "exec"), ns)
        return await ns["completion"](
            req=CompletionReq(conversation_id="conversation", user_input="问题"),
            login_user=SimpleNamespace(user_id="user"),
            request=SimpleNamespace(headers={"x-agentchat-protocol": "ag-ui/1.0"}),
        )

    async def test_http_finishes_before_slow_memory_and_summary(self):
        ended, started, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

        async def slow_memory(*args, **kwargs):
            started.set()
            await release.wait()

        response = await self.make_response(slow_memory)
        frames = []

        async def send(message):
            if message["type"] == "http.response.body":
                frames.append(message.get("body", b""))
                if not message.get("more_body", False):
                    ended.set()

        async def receive():
            await asyncio.Event().wait()

        task = asyncio.create_task(response({"type": "http", "asgi": {"spec_version": "2.4"}}, receive, send))
        try:
            await asyncio.wait_for(ended.wait(), 2)
            await asyncio.wait_for(started.wait(), 2)
            self.assertIn(b"RUN_FINISHED", b"".join(frames))
            self.assertEqual(self.history.save_chat_history.await_count, 2)
            self.assertEqual(self.history.save_chat_history.call_args.kwargs["content"], "回答")
            self.conversation.update_conversation_summary.assert_not_awaited()
        finally:
            release.set()
            await asyncio.wait_for(task, 2)
        self.conversation.update_conversation_summary.assert_awaited_once()

    async def test_cancelled_stream_keeps_history_without_postprocessing(self):
        memory = AsyncMock()
        response = await self.make_response(memory)
        while "TEXT_MESSAGE_CONTENT" not in await anext(response.body_iterator):
            pass
        await response.body_iterator.aclose()
        await response.background()
        self.assertEqual(self.history.save_chat_history.call_args.kwargs["content"], "回答")
        memory.assert_not_awaited()
        self.conversation.update_conversation_summary.assert_not_awaited()
