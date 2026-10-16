"""验证真实用量归属、并发隔离与重复计数防护。"""
import ast
import asyncio
import tempfile
import unittest
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from agentchat.settings import app_settings
from fastapi import Depends
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

app_settings.database = {
    "url": "sqlite:///:memory:",
}
from agentchat.api.responses.builder import resp_200, resp_500
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.core.callbacks.usage_metadata import UsageMetadataCallbackHandler
from agentchat.core.models.usage_model import ChatModelWithTokenUsage
from agentchat.database.models.usage_stats import UsageStats
from agentchat.utils.contexts import (
    set_agent_name_context,
    set_conversation_id_context,
    set_user_id_context,
)


def result(model="test-model", input_tokens=100, output_tokens=20, model_key="model_name"):
    return LLMResult(
        generations=[
            [
                ChatGeneration(
                    message=AIMessage(
                        content="回复",
                        response_metadata={
                            model_key: model,
                        },
                        usage_metadata={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens,
                        },
                    )
                )
            ]
        ]
    )


class ConversationUsageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        path = Path(self.directory.name) / "usage.db"
        self.sync_engine = create_engine(
            f"sqlite:///{path.as_posix()}",
            connect_args={
                "check_same_thread": False,
            },
        )
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

        self.patches = [patch("agentchat.database.dao.usage_stats.session_getter", sync_session),
                        patch("agentchat.database.dao.usage_stats.async_session_getter", async_session)]
        for item in self.patches:
            item.start()
        set_user_id_context("user")
        set_agent_name_context("资料助手")
        set_conversation_id_context("conversation-a")

    async def asyncTearDown(self):
        for item in reversed(self.patches):
            item.stop()
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        self.directory.cleanup()
        set_user_id_context(None)
        set_agent_name_context(None)
        set_conversation_id_context(None)

    def rows(self):
        with Session(self.sync_engine) as session:
            return session.exec(select(UsageStats)).all()

    async def test_callback_links_conversation_and_deduplicates_same_run(self):
        handler = UsageMetadataCallbackHandler()
        run_id = uuid4()
        handler.on_llm_end(result(), run_id=run_id)
        handler.on_llm_end(result(), run_id=run_id)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].user_id, rows[0].conversation_id, rows[0].agent), ("user", "conversation-a", "资料助手"))
        self.assertEqual((rows[0].input_tokens, rows[0].output_tokens), (100, 20))

    async def test_provider_model_alias_and_raw_usage_are_supported(self):
        handler = UsageMetadataCallbackHandler()
        handler.on_llm_end(result(model_key="model"), run_id=uuid4())
        handler.on_llm_end(
            LLMResult(
                generations=[],
                llm_output={
                    "model_name": "raw-model",
                    "token_usage": {
                        "prompt_tokens": 50,
                        "completion_tokens": 10,
                    },
                },
            ),
            run_id=uuid4(),
        )
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(row.input_tokens + row.output_tokens for row in rows), 180)

    async def test_parallel_requests_and_worker_threads_keep_separate_contexts(self):
        handler = UsageMetadataCallbackHandler()

        async def record(user_id, conversation_id):
            set_user_id_context(user_id)
            set_conversation_id_context(conversation_id)
            set_agent_name_context("助手" + user_id)
            await asyncio.sleep(0)
            await asyncio.to_thread(handler.on_llm_end, result(), run_id=uuid4())

        await asyncio.gather(record("user-a", "conversation-a"), record("user-b", "conversation-b"))
        self.assertEqual({(row.user_id, row.conversation_id, row.agent) for row in self.rows()},
                         {("user-a", "conversation-a", "助手user-a"), ("user-b", "conversation-b", "助手user-b")})

    async def test_aggregation_keeps_all_agents_but_excludes_other_users_and_legacy_rows(self):
        UsageStatsService.sync_create_usage_stats("资料助手", "model-a", "user", 100, 20, "conversation-a")
        UsageStatsService.sync_create_usage_stats("代码助手", "model-b", "user", 50, 10, "conversation-a")
        UsageStatsService.sync_create_usage_stats("其他助手", "model-a", "other", 1000, 1000, "conversation-a")
        UsageStatsService.sync_create_usage_stats("旧记录", "legacy", "user", 1000, 1000)
        totals = await UsageStatsService.get_conversation_usage("user", ["conversation-a", "unknown"])
        self.assertEqual(
            totals["conversation-a"],
            {
                "input_tokens": 150,
                "output_tokens": 30,
                "total_tokens": 180,
                "model_calls": 2,
                "usage_available": True,
            },
        )
        self.assertNotIn("unknown", totals)
        self.assertEqual(await UsageStatsService.get_conversation_usage("user", []), {})
        filtered = await UsageStatsService.get_usage_by_agent_model("user", conversation_id="conversation-a")
        total = sum(value["total_tokens"] for day in filtered.values() for value in day["model"].values())
        self.assertEqual(total, 180)
        counts = await UsageStatsService.get_usage_count_by_agent_model("user", conversation_id="conversation-a")
        self.assertEqual(sum(value for day in counts.values() for value in day["model"].values()), 2)
        all_usage = await UsageStatsService.get_usage_by_agent_model("user")
        self.assertEqual(sum(value["total_tokens"] for day in all_usage.values() for value in day["model"].values()), 2180)

    async def test_custom_model_records_once_and_does_not_cache_request_identity(self):
        model = ChatModelWithTokenUsage(model="custom-model", api_key="test-key", base_url="https://example.com/v1")
        model._record_token_usage_dict(4, 2)
        set_user_id_context("other-user")
        set_conversation_id_context("conversation-b")
        model._record_token_usage_dict(5, 3)
        UsageMetadataCallbackHandler().on_llm_end(
            LLMResult(
                generations=[],
                llm_output={
                    "model_name": "custom-model",
                    "usage_recorded": True,
                    "token_usage": {
                        "prompt_tokens": 5,
                        "completion_tokens": 3,
                    },
                },
            )
        )
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual({(row.user_id, row.conversation_id) for row in rows}, {("user", "conversation-a"), ("other-user", "conversation-b")})
        self.assertIsNone(model.user_id)
        self.assertIsNone(model.agent_name)

    async def test_no_reported_usage_is_not_replaced_with_estimates(self):
        handler = UsageMetadataCallbackHandler()
        handler.on_llm_end(
            LLMResult(
                generations=[
                    [ChatGeneration(message=AIMessage(content="长回复" * 100))]
                ],
                llm_output={
                    "model_name": "unknown",
                },
            )
        )
        self.assertEqual(self.rows(), [])

    async def test_statistics_storage_failure_does_not_interrupt_model_callback(self):
        with patch.object(UsageStatsService, "sync_create_usage_stats", side_effect=RuntimeError):
            UsageMetadataCallbackHandler().on_llm_end(result(), run_id=uuid4())
            model = ChatModelWithTokenUsage(model="custom-model", api_key="test-key", base_url="https://example.com/v1")
            model._record_token_usage_dict(4, 2)
        self.assertEqual(self.rows(), [])

    async def test_conversation_list_returns_cumulative_usage_and_preserves_topic_title(self):
        UsageStatsService.sync_create_usage_stats("资料助手", "model-a", "user", 100, 20, "conversation-a")
        UsageStatsService.sync_create_usage_stats("代码助手", "model-b", "user", 50, 10, "conversation-a")
        conversations = [
            {
                "conversation_id": "conversation-a",
                "agent_id": "a",
                "name": "工作计划",
            },
            {
                "conversation_id": "conversation-b",
                "agent_id": "b",
                "name": "另一个话题",
            },
        ]
        # 直接执行真实接口函数，仅替换登录与智能体查询，统计仍走隔离数据库。
        source = Path(__file__).resolve().parents[1] / "agentchat/api/v1/conversation.py"
        tree = ast.parse(source.read_text(encoding="utf8"))
        tree.body = [node for node in tree.body if getattr(node, "name", None) == "get_conversation"]
        tree.body[0].decorator_list = []
        namespace = dict(
            Depends=Depends,
            UserPayload=SimpleNamespace,
            get_login_user=lambda: None,
            ConversationService=SimpleNamespace(
                get_list_conversation=AsyncMock(return_value=conversations),
                conversation_title_pending=lambda value: False,
            ),
            AgentService=SimpleNamespace(
                select_agent_by_id=AsyncMock(
                    return_value={
                        "name": "当前智能体",
                    }
                )
            ),
            UsageStatsService=UsageStatsService,
            resp_200=resp_200,
            resp_500=resp_500,
        )
        exec(compile(tree, str(source), "exec"), namespace)
        response = await namespace["get_conversation"](SimpleNamespace(user_id="user"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "工作计划")
        self.assertEqual(response.data[0]["total_tokens"], 180)
        self.assertEqual(response.data[0]["model_calls"], 2)
        self.assertTrue(response.data[0]["usage_available"])
        self.assertFalse(response.data[1]["usage_available"])


if __name__ == "__main__":
    unittest.main()
