"""在隔离数据库中验证会话切换、身份保留和异步标题，不调用真实模型。"""
import ast
import asyncio
import json
import tempfile
import unittest
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import List
from unittest.mock import AsyncMock, patch

from agentchat.settings import app_settings
from fastapi import Depends, HTTPException
from starlette.background import BackgroundTask
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

app_settings.database = {
    "url": "sqlite:///:memory:",
}
from agentchat.api.responses.streaming import WatchedStreamingResponse
from agentchat.api.services import conversation as conversation_title
from agentchat.api.services.agent import AgentService
from agentchat.api.services.conversation import ConversationService
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.core.callbacks.usage_metadata import UsageMetadataCallbackHandler
from agentchat.database.dao.agent import AgentDao
from agentchat.database.dao.conversation import ConversationDao
from agentchat.database.dao.history import HistoryDao
from agentchat.database.models.agent import AgentTable
from agentchat.database.models.conversation import ConversationTable
from agentchat.schemas.completion import CompletionReq
from agentchat.utils.chat_attachments import attachment_events
from agentchat.utils.contexts import (
    set_agent_name_context,
    set_conversation_id_context,
    set_user_id_context,
)
from agentchat.utils.conversation_title import normalize_conversation_title
from langchain_core.outputs import ChatGeneration, LLMResult

ROOT = Path(__file__).resolve().parents[1] / "agentchat"


def load_definition(path, name, namespace):
    tree = ast.parse(path.read_text(encoding="utf8"))
    tree.body = [node for node in tree.body if getattr(node, "name", None) == name]
    for node in tree.body:
        node.decorator_list = []
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace[name]


class FlexibleConversationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        path = Path(self.directory.name) / "conversations.db"
        self.sync_engine = create_engine(f"sqlite:///{path.as_posix()}")
        SQLModel.metadata.create_all(self.sync_engine)
        self.async_engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")
        sessions = async_sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)

        @contextmanager
        def sync_session():
            with Session(self.sync_engine) as session:
                yield session

        @asynccontextmanager
        async def async_session():
            async with sessions() as session:
                yield session

        self.patches = [patch("agentchat.database.dao.agent.session_getter", sync_session),
                        patch("agentchat.database.dao.conversation.async_session_getter", async_session),
                        patch("agentchat.database.dao.history.async_session_getter", async_session),
                        patch("agentchat.database.dao.usage_stats.async_session_getter", async_session),
                        patch("agentchat.database.dao.usage_stats.session_getter", sync_session)]
        for item in self.patches:
            item.start()
        await AgentDao.create_agent(AgentTable(id="agent-a", name="资料助手", user_id="user", logo_url="/a.svg", enable_memory=False))
        await AgentDao.create_agent(AgentTable(id="agent-b", name="代码助手", user_id="user", logo_url="/b.svg", enable_memory=False))
        await AgentDao.create_agent(AgentTable(id="private", name="私人助手", user_id="other", logo_url="", enable_memory=False))
        self.conversation = await ConversationDao.create_conversation("新会话", "agent-a", "Agent", "user")
        ns = dict(
            List=List,
            BaseMessage=BaseMessage,
            AIMessage=AIMessage,
            HumanMessage=HumanMessage,
            HistoryDao=HistoryDao,
            ConversationDao=ConversationDao,
            AgentService=AgentService,
            Assistant_Role="assistant",
            User_Role="user",
            AdminUser="1",
        )
        self.history = load_definition(ROOT / "api/services/history.py", "HistoryService", ns)

    async def asyncTearDown(self):
        await ConversationService.stop_conversation_title_tasks()
        for item in reversed(self.patches):
            item.stop()
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        self.directory.cleanup()
        set_user_id_context(None)
        set_agent_name_context(None)
        set_conversation_id_context(None)

    async def save(self, role, content, events=None):
        return await HistoryDao.create_history(role, content, events or [], self.conversation.conversation_id)

    async def test_switch_keeps_conversation_title_history_and_original_reply_identity(self):
        await self.save("user", "帮我整理工作计划")
        await self.save("assistant", "原回复")
        before = await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)
        result = await ConversationService.switch_agent(self.conversation.conversation_id, "agent-b", "user")
        self.assertEqual(result["conversation_id"], self.conversation.conversation_id)
        self.assertEqual(result["name"], before.name)
        self.assertEqual(result["create_time"], before.create_time.isoformat())
        history = await HistoryDao.get_conversation_history(self.conversation.conversation_id)
        self.assertEqual([item.content for item in history], ["帮我整理工作计划", "原回复"])
        self.assertEqual(history[-1].events[0]["data"]["agent_id"], "agent-a")
        context = await self.history.get_short_term_messages(self.conversation.conversation_id, "user")
        self.assertEqual([message.content for message in context], ["帮我整理工作计划", "原回复"])

    async def test_first_message_flag_and_title_length(self):
        first = await self.save("user", "这个问题需要一个很长很长很长的讨论标题")
        second = await self.save("user", "第二个问题")
        self.assertTrue(first["first_user"])
        self.assertFalse(second["first_user"])
        self.assertTrue(2 <= len(first["title"]) <= 10)
        self.assertEqual((await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)).name, first["title"])
        for text in ["标题：『代码审查』", "  研究报告\n解释", "abcdefghijklmnop"]:
            self.assertTrue(2 <= len(normalize_conversation_title(text)) <= 10)
        self.assertEqual(normalize_conversation_title("！"), "")

    async def test_concurrent_first_messages_claim_title_once(self):
        results = await asyncio.gather(self.save("user", "首个问题"), self.save("user", "另一个问题"))
        self.assertEqual(sum(result["first_user"] for result in results), 1)

    async def test_permissions_checked_before_switching(self):
        for user, agent_id in [("other", "agent-b"), ("user", "private"), ("user", "missing")]:
            with self.assertRaises(ValueError):
                await ConversationService.resolve_agent(self.conversation.conversation_id, user, agent_id)
        self.assertEqual((await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)).agent_id, "agent-a")
        with self.assertRaises(ValueError):
            await ConversationService.verify_user_permission("missing-conversation", "user")

    async def test_delete_agent_preserves_history_and_allows_another_agent(self):
        await self.save("user", "整理资料")
        await self.save("assistant", "已整理")
        await AgentService.delete_agent_by_id("agent-a")
        conversation = await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)
        self.assertEqual(conversation.agent_id, "")
        self.assertEqual(len(await HistoryDao.get_conversation_history(conversation.conversation_id)), 2)
        result = await ConversationService.resolve_agent(self.conversation.conversation_id, "user", "agent-b")
        self.assertEqual(result["id"], "agent-b")

    async def test_title_background_does_not_wait_and_keeps_activity_time(self):
        first = await self.save("user", "帮我制定下一周的工作计划")
        before = await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)
        started, release = asyncio.Event(), asyncio.Event()

        async def invoke(*args, **kwargs):
            started.set()
            await release.wait()
            return SimpleNamespace(content="每周工作计划")

        with patch.object(conversation_title.ModelManager, "get_chat_model", return_value=SimpleNamespace(ainvoke=invoke)):
            ConversationService.queue_conversation_title(self.conversation.conversation_id, "帮我制定下一周的工作计划", first["title"])
            await asyncio.wait_for(started.wait(), 1)
            self.assertTrue(ConversationService.conversation_title_pending(self.conversation.conversation_id))
            await ConversationService.switch_agent(self.conversation.conversation_id, "agent-b", "user")
            switched = await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)
            release.set()
            await asyncio.gather(*list(ConversationService._tasks.values()))
        result = await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)
        self.assertEqual(result.name, "每周工作计划")
        self.assertEqual(result.update_time, switched.update_time)
        self.assertEqual(result.create_time, before.create_time)

    async def test_title_failure_and_late_result_do_not_overwrite(self):
        first = await self.save("user", "整理下一周的工作任务")
        with patch.object(conversation_title.ModelManager, "get_chat_model", return_value=SimpleNamespace(ainvoke=AsyncMock(side_effect=RuntimeError))):
            ConversationService.queue_conversation_title(self.conversation.conversation_id, "整理下一周的工作任务", first["title"])
            await asyncio.gather(*list(ConversationService._tasks.values()))
        self.assertEqual((await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)).name, first["title"])
        await ConversationDao.update_title_if_unchanged(self.conversation.conversation_id, first["title"], "人工标题")
        await ConversationDao.update_title_if_unchanged(self.conversation.conversation_id, first["title"], "迟到的标题")
        self.assertEqual((await ConversationDao.select_conversation_by_id(self.conversation.conversation_id)).name, "人工标题")

    async def test_two_agents_reply_in_one_conversation_and_stream_identity_is_fixed(self):
        configs, inputs, queued = [], [], []

        class FakeAgent:
            def __init__(self, config):
                self.config = config
                configs.append(config.name)
            async def init_agent(self):
                pass
            def stop_streaming_callback(self):
                pass
            async def astream(self, messages):
                inputs.append([message.content for message in messages])
                yield {
                    "type": "response_chunk",
                    "data": {
                        "chunk": self.config.name + "回复",
                    },
                }
                UsageMetadataCallbackHandler().on_llm_end(
                    LLMResult(
                        generations=[
                            [
                                ChatGeneration(
                                    message=AIMessage(
                                        content="回复",
                                        response_metadata={
                                            "model_name": "test-model",
                                        },
                                        usage_metadata={
                                            "input_tokens": 5,
                                            "output_tokens": 2,
                                            "total_tokens": 7,
                                        },
                                    )
                                )
                            ]
                        ]
                    )
                )

        from agentchat.protocols.ag_ui import protocol_stream
        from fastapi import Request
        ns = dict(
            Request=Request,
            BackgroundTask=BackgroundTask,
            protocol_stream=protocol_stream,
            CompletionReq=CompletionReq,
            UserPayload=SimpleNamespace,
            Depends=Depends,
            get_login_user=lambda: None,
            HTTPException=HTTPException,
            ConversationService=ConversationService,
            HistoryService=self.history,
            AgentConfig=lambda **data: SimpleNamespace(**data),
            GeneralAgent=FakeAgent,
            set_user_id_context=set_user_id_context,
            set_agent_name_context=set_agent_name_context,
            set_conversation_id_context=set_conversation_id_context,
            bind_log_context=lambda **fields: None,
            build_completion_user_input=lambda file_url, user_input: user_input,
            build_completion_system_prompt=lambda system, summary, memory: system,
            SYSTEM_PROMPT="通用提示词",
            List=List,
            BaseMessage=BaseMessage,
            SystemMessage=SystemMessage,
            HumanMessage=HumanMessage,
            json=json,
            attachment_events=attachment_events,
            count_tokens_usage=lambda value: 1,
            WatchedStreamingResponse=WatchedStreamingResponse,
        )
        completion = load_definition(ROOT / "api/v1/completion.py", "completion", ns)
        with patch.object(ConversationService, "queue_conversation_title", side_effect=lambda *args: queued.append(args)):
            response = await completion(req=CompletionReq(conversation_id=self.conversation.conversation_id, agent_id="agent-a", user_input="首个问题"), login_user=SimpleNamespace(user_id="user"))
        # 在第一轮流结束前切换下一轮智能体，本轮身份仍固定为原智能体。
        await ConversationService.switch_agent(self.conversation.conversation_id, "agent-b", "user")
        frames = [frame async for frame in response.body_iterator]
        self.assertIn('agent-a', frames[0])
        response = await completion(
            req=CompletionReq(
                conversation_id=self.conversation.conversation_id,
                agent_id="agent-b",
                user_input="继续讨论",
            ),
            login_user=SimpleNamespace(user_id="user"),
            request=SimpleNamespace(
                headers={
                    "x-agentchat-protocol": "ag-ui/1.0",
                }
            ),
        )
        frames = [frame async for frame in response.body_iterator]
        self.assertIn('RUN_STARTED', frames[0])
        self.assertIn('agent-b', frames[1])
        self.assertIn('RUN_FINISHED', frames[-1])
        self.assertEqual(configs, ["资料助手", "代码助手"])
        self.assertIn("资料助手回复", inputs[-1])
        self.assertEqual(len(queued), 1)
        history = await HistoryDao.get_conversation_history(self.conversation.conversation_id)
        self.assertEqual(len(history), 4)
        self.assertEqual([row.events[0]["data"]["agent_id"] for row in history if row.role == "assistant"], ["agent-a", "agent-b"])
        usage = await UsageStatsService.get_conversation_usage("user", [self.conversation.conversation_id])
        self.assertEqual(usage[self.conversation.conversation_id]["total_tokens"], 14)
        self.assertEqual(usage[self.conversation.conversation_id]["model_calls"], 2)


if __name__ == "__main__":
    unittest.main()
