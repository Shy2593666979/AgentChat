import asyncio
import unittest
from types import SimpleNamespace

from agentchat.settings import app_settings, init_app_settings
from langchain_core.messages import ToolMessage

asyncio.run(init_app_settings())
app_settings.database = {
    "url": "sqlite:///:memory:",
}

from agentchat.services.mars.mars_agent import MarsAgent, MarsConfig


class EmptyReasoningModel:
    async def astream(self, messages):
        async def chunks():
            if False:
                yield None
        return chunks()


class MarsStreamTests(unittest.IsolatedAsyncioTestCase):
    def agent(self, react_agent):
        agent = MarsAgent(MarsConfig(user_id="test-user"))
        agent.react_agent = react_agent
        agent.reasoning_model = EmptyReasoningModel()
        return agent

    async def test_tool_messages_and_error_status_are_preserved(self):
        for status in ("success", "error"):
            agent = MarsAgent(MarsConfig(user_id="test-user"))
            agent.mars_output_queue = asyncio.Queue()
            agent.reasoning_interrupt = asyncio.Event()
            middleware = (await agent.setup_middlewares())[-1]
            message = ToolMessage(content="工具返回内容", tool_call_id="tool-1", status=status)
            async def handler(request):
                return message
            request = SimpleNamespace(
                tool_call={
                    "name": "deep_search",
                    "id": "tool-1",
                    "args": {},
                }
            )
            result = await middleware.awrap_tool_call(request, handler)
            self.assertIs(result, message)
            self.assertEqual(request.tool_call["args"]["user_id"], "test-user")
            self.assertEqual((await agent.mars_output_queue.get())["type"], "tool_start")
            self.assertEqual((await agent.mars_output_queue.get())["type"], "tool_end" if status == "success" else "tool_error")

    async def test_drains_all_events_before_finishing(self):
        class FakeAgent:
            async def astream(self, **kwargs):
                for event in (
                    {
                        "type": "tool_start",
                        "data": {
                            "id": "search",
                        },
                    },
                    {
                        "type": "response_chunk",
                        "data": "结果正文",
                    },
                    {
                        "type": "tool_end",
                        "data": {
                            "id": "search",
                        },
                    },
                ):
                    yield "custom", event
        events = [event async for event in self.agent(FakeAgent()).ainvoke_stream([])]
        self.assertEqual([event["type"] for event in events], ["tool_start", "response_chunk", "tool_end"])

    async def test_execution_error_is_sent_instead_of_hanging(self):
        class FailedAgent:
            async def astream(self, **kwargs):
                raise RuntimeError("test failure")
                yield
        async def collect():
            return [event async for event in self.agent(FailedAgent()).ainvoke_stream([])]
        events = await asyncio.wait_for(collect(), timeout=2)
        self.assertEqual(events[0]["type"], "error")

    async def test_tool_progress_does_not_wait_for_blocked_reasoning(self):
        class BlockedReasoning:
            async def astream(self, messages):
                await asyncio.Event().wait()
        class FakeAgent:
            async def astream(self, **kwargs):
                await asyncio.sleep(0)
                yield "custom", {
                    "type": "tool_start",
                    "data": {
                        "id": "tool",
                    },
                }
                yield "custom", {
                    "type": "response_chunk",
                    "data": "正文",
                }
        agent = self.agent(FakeAgent())
        agent.reasoning_model = BlockedReasoning()
        async def collect():
            return [event async for event in agent.ainvoke_stream([])]
        events = await asyncio.wait_for(collect(), timeout=2)
        self.assertEqual([event["type"] for event in events], ["tool_start", "response_chunk"])

    async def test_agent_error_also_cancels_blocked_reasoning(self):
        class BlockedReasoning:
            async def astream(self, messages):
                await asyncio.Event().wait()
        class FailedAgent:
            async def astream(self, **kwargs):
                await asyncio.sleep(0)
                raise RuntimeError("test failure")
                yield
        agent = self.agent(FailedAgent())
        agent.reasoning_model = BlockedReasoning()
        async def collect():
            return [event async for event in agent.ainvoke_stream([])]
        events = await asyncio.wait_for(collect(), timeout=2)
        self.assertEqual(events[0]["type"], "error")

    async def test_closing_stream_cancels_background_execution(self):
        cancelled = asyncio.Event()
        class WaitingAgent:
            async def astream(self, **kwargs):
                try:
                    yield "custom", {
                        "type": "progress_chunk",
                        "data": {
                            "message": "开始执行",
                        },
                    }
                    await asyncio.Event().wait()
                finally:
                    cancelled.set()
        stream = self.agent(WaitingAgent()).ainvoke_stream([])
        await anext(stream)
        await stream.aclose()
        self.assertTrue(cancelled.is_set())


if __name__ == "__main__":
    unittest.main()
