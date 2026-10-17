import unittest
from unittest.mock import patch

from agentchat.services.mars.events import (
    deep_search_event,
    get_mars_writer,
    mars_tool_id,
    stream_search_report,
)


class MarsEventTests(unittest.TestCase):
    def test_progress_is_bound_to_current_tool_and_context_is_restored(self):
        emitted = []
        with patch('langgraph.config.get_stream_writer', return_value=emitted.append):
            writer = get_mars_writer()
            for identity in ('knowledge', 'news'):
                token = mars_tool_id.set(identity)
                try:
                    writer(
                        {
                            'type': 'progress_chunk',
                            'data': {
                                'message': '执行步骤',
                            },
                        }
                    )
                finally:
                    mars_tool_id.reset(token)
        self.assertEqual([event['tool_id'] for event in emitted], ['knowledge', 'news'])
        self.assertEqual(mars_tool_id.get(), '')
    def test_execution_updates_do_not_become_report_text(self):
        for state in ("start", "complete", "error"):
            event = deep_search_event(
                {
                    "type": state,
                    "node": "web_research",
                    "content": "搜索状态",
                }
            )
            self.assertEqual(event["type"], "progress_chunk")
            self.assertEqual(
                event["data"],
                {
                    "node": "web_research",
                    "status": state,
                    "message": "搜索状态",
                },
            )

    def test_report_stream_remains_exact_markdown(self):
        content = "## 路线\n\n[来源](https://example.com)"
        self.assertEqual(
            deep_search_event(
                {
                    "type": "streaming",
                    "content": content,
                }
            )["data"],
            content,
        )

    def test_final_snapshot_does_not_duplicate_streamed_report(self):
        self.assertIsNone(
            deep_search_event(
                {
                    "type": "final_result",
                    "content": "完整正文",
                }
            )
        )
        self.assertIsNone(
            deep_search_event(
                {
                    "type": "streaming",
                    "content": "",
                }
            )
        )


class SearchReportTests(unittest.IsolatedAsyncioTestCase):
    async def test_report_is_returned_to_model_without_reemitting_snapshot(self):
        class Graph:
            async def run_with_streaming(self, messages):
                for chunk in [
                    {
                        "type": "start",
                        "node": "finalize_answer",
                        "content": "开始生成",
                    },
                    {
                        "type": "streaming",
                        "content": "# 泰山攻略\n",
                    },
                    {
                        "type": "streaming",
                        "content": "完整正文",
                    },
                    {
                        "type": "final_result",
                        "content": "# 泰山攻略\n完整正文",
                    },
                ]:
                    yield chunk
        emitted = []
        result = await stream_search_report(Graph(), [], emitted.append)
        self.assertEqual(result, "# 泰山攻略\n完整正文")
        self.assertEqual("".join(event["data"] for event in emitted if event["type"] == "response_chunk"), result)
        self.assertEqual(emitted[0]["type"], "result_start")

    async def test_new_report_has_explicit_replacement_boundary(self):
        class Graph:
            async def run_with_streaming(self, messages):
                for report in ("第一版完整攻略", "第二版完整攻略"):
                    yield {
                        "type": "start",
                        "node": "finalize_answer",
                        "content": "生成报告",
                    }
                    yield {
                        "type": "streaming",
                        "content": report,
                    }
        emitted = []
        self.assertEqual(await stream_search_report(Graph(), [], emitted.append), "第二版完整攻略")
        self.assertEqual(sum(event["type"] == "result_start" for event in emitted), 2)


if __name__ == "__main__":
    unittest.main()
