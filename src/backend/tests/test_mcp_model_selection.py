import asyncio
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch

from agentchat.settings import app_settings
from fastapi import HTTPException
from langgraph.types import Command

app_settings.database = {
    "url": "sqlite:///:memory:",
}
app_settings.multi_models = SimpleNamespace(chat_model=SimpleNamespace(
    model_name="test-model", api_key="test-key", base_url="https://example.com/v1"
))

from agentchat.api.services.mcp_model import resolve_mcp_model

# 本组检查不执行服务注册，避免加载对象存储或连接真实 MCP 服务。
registration_stub = ModuleType("agentchat.mcp_proxy.register_mcp")
registration_stub.RegisterMcpService = object
with patch.dict(
    "sys.modules",
    {
        "agentchat.mcp_proxy.register_mcp": registration_stub,
    },
):
    from agentchat.mcp_proxy.agent import (
        AbstractMcpAgent,
        _chat_model,
        _mcp_model_context,
    )


class McpModelSelectionTests(unittest.IsolatedAsyncioTestCase):
    def task(self, messages=None, user_id="1"):
        return SimpleNamespace(user_id=user_id, messages=messages or [])

    def model(self, user_id="0", llm_type="LLM"):
        return SimpleNamespace(user_id=user_id, llm_type=llm_type, model="selected-model", api_key="test-key", base_url="https://example.com/v1")

    async def test_visible_model_is_used(self):
        with patch("agentchat.api.services.mcp_model.LLMDao.get_llm_by_id", AsyncMock(return_value=self.model())), patch("agentchat.api.services.mcp_model.ModelManager.get_user_model", return_value="client") as factory:
            self.assertEqual(await resolve_mcp_model(self.task(), "1", "selected"), ("selected", "client"))
            self.assertEqual(factory.call_args.kwargs["model"], "selected-model")

    async def test_hidden_or_wrong_type_model_is_rejected(self):
        for model, code in [(self.model(user_id="2"), 403), (self.model(llm_type="Embedding"), 400), (None, 404)]:
            with patch("agentchat.api.services.mcp_model.LLMDao.get_llm_by_id", AsyncMock(return_value=model)):
                with self.assertRaises(HTTPException) as error:
                    await resolve_mcp_model(self.task(), "1", "selected")
                self.assertEqual(error.exception.status_code, code)

    async def test_other_users_task_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            await resolve_mcp_model(self.task(user_id="2"), "1", "selected")
        self.assertEqual(error.exception.status_code, 403)

    async def test_legacy_request_keeps_default(self):
        self.assertEqual(await resolve_mcp_model(self.task(), "1"), (None, None))

    async def test_resume_keeps_saved_model_and_blocks_switch(self):
        task = self.task(
            [
                {
                    "model_id": "selected",
                    "content": [
                        {
                            "type": "interrupt",
                            "data": {
                                "status": False,
                                "allowed_decisions": ["approve", "reject"],
                            },
                        }
                    ],
                }
            ]
        )
        with patch("agentchat.api.services.mcp_model.LLMDao.get_llm_by_id", AsyncMock(return_value=self.model())), patch("agentchat.api.services.mcp_model.ModelManager.get_user_model", return_value="client"):
            self.assertEqual(await resolve_mcp_model(task, "1", decision="reject"), ("selected", "client"))
        with self.assertRaises(HTTPException) as error:
            await resolve_mcp_model(task, "1", "another", "approve")
        self.assertEqual(error.exception.status_code, 409)
        with self.assertRaises(HTTPException):
            await resolve_mcp_model(task, "1", "selected")

    async def test_processed_confirmation_cannot_resume(self):
        task = self.task(
            [
                {
                    "content": [
                        {
                            "type": "interrupt",
                            "data": {
                                "status": False,
                            },
                        },
                        {
                            "type": "interrupt",
                            "data": {
                                "status": True,
                            },
                        },
                    ],
                }
            ]
        )
        with self.assertRaises(HTTPException):
            await resolve_mcp_model(task, "1", decision="approve")

    async def test_parallel_streams_and_resume_keep_tool_model_context(self):
        seen = []

        class Graph:
            async def astream(self, *args, **kwargs):
                first = _chat_model()
                await asyncio.sleep(0)
                worker = await asyncio.to_thread(_chat_model)
                seen.append((first, worker))
                yield "custom", {
                    "title": "test",
                    "status": "END",
                }

        agent = AbstractMcpAgent.__new__(AbstractMcpAgent)
        agent.agent = Graph()
        agent._create_agent = lambda model: Graph()
        model_a, model_b = object(), object()

        async def consume(model):
            return [event async for event in agent.astream([], "test", model=model)]

        await asyncio.gather(consume(model_a), consume(model_b))
        self.assertTrue(all(first is worker for first, worker in seen))
        self.assertEqual({id(first) for first, _ in seen}, {id(model_a), id(model_b)})
        self.assertIsNone(_mcp_model_context.get())
        _ = [event async for event in agent.astream_resume(Command(resume={}), "test", model=model_a)]
        self.assertIs(seen[-1][0], model_a)
        self.assertIsNone(_mcp_model_context.get())


if __name__ == "__main__":
    unittest.main()
