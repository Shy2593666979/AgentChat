"""SpecStream 搜索工具的离线测试：请求参数、结果格式和错误信息（不访问网络）。

运行方式（在 src/backend 目录下）：
    python -m pytest tests/test_specstream_search.py -q
"""

import asyncio
import unittest
from unittest import mock

import requests

from agentchat.settings import app_settings, init_app_settings

asyncio.run(init_app_settings())
app_settings.database = {"url": "sqlite:///:memory:"}

from agentchat.tools import AgentTools, AgentToolsWithName, WeChatTools
from agentchat.tools.web_search.specstream_search import action
from agentchat.tools.web_search.specstream_search.action import specstream_search


def fake_response(status: int, payload=None, text: str = ""):
    response = mock.Mock(status_code=status, text=text)
    if isinstance(payload, Exception):
        response.json.side_effect = payload
    else:
        response.json.return_value = payload
    return response


SOURCES = {
    "data": {
        "answer": None,
        "rows": [{"name": "row view, not used"}],
        "sources": [
            {
                "title": "Python 3.13 release notes",
                "url": "https://docs.python.org/3/whatsnew/3.13.html",
                "snippet": "Python 3.13 adds an experimental free-threaded build.",
                "published": "2024-10-07",
            },
            {"title": "", "url": "https://peps.python.org/pep-0703/", "snippet": "PEP 703"},
        ],
    }
}


class SpecStreamSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.object(app_settings.tools, "specstream", {"api_key": " test-key "})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_tool(self, response, **kwargs):
        with mock.patch.object(action.requests, "get", return_value=response) as get:
            result = specstream_search.invoke({"query": "python free threading", **kwargs})
        return result, get

    def test_request_shape(self) -> None:
        _, get = self.run_tool(fake_response(200, SOURCES), max_results=50)
        url = get.call_args.args[0]
        kwargs = get.call_args.kwargs
        self.assertEqual(url, "https://api.specstream.ai/v1/web-search")
        self.assertEqual(kwargs["params"], {"q": "python free threading", "num": 20})
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["timeout"], 30)

    def test_formats_sources_with_url_snippet_and_date(self) -> None:
        result, _ = self.run_tool(fake_response(200, SOURCES), max_results=5)
        self.assertIn("[1] Python 3.13 release notes", result)
        self.assertIn("网址: https://docs.python.org/3/whatsnew/3.13.html", result)
        self.assertIn("发布时间: 2024-10-07", result)
        self.assertIn("[2] 结果 2", result)
        self.assertNotIn("row view", result)

    def test_respects_max_results(self) -> None:
        result, get = self.run_tool(fake_response(200, SOURCES), max_results=1)
        self.assertEqual(get.call_args.kwargs["params"]["num"], 1)
        self.assertNotIn("[2]", result)

    def test_no_key_sends_nothing(self) -> None:
        with mock.patch.object(app_settings.tools, "specstream", {"api_key": ""}):
            with mock.patch.object(action.requests, "get") as get:
                result = specstream_search.invoke({"query": "anything"})
        get.assert_not_called()
        self.assertIn("未配置", result)

    def test_errors_do_not_echo_the_key(self) -> None:
        cases = {
            401: "无效",
            402: "余额不足",
            429: "频率超限",
            500: "Status 500",
        }
        for status, expected in cases.items():
            result, _ = self.run_tool(fake_response(status, text="Bearer test-key"))
            self.assertIn(expected, result)
            self.assertNotIn("test-key", result)

    def test_bad_json_and_empty_results(self) -> None:
        result, _ = self.run_tool(fake_response(200, ValueError("not json")))
        self.assertIn("非 JSON", result)
        result, _ = self.run_tool(fake_response(200, {"data": {"sources": []}}))
        self.assertEqual(result, "未找到相关结果")

    def test_network_error(self) -> None:
        with mock.patch.object(action.requests, "get", side_effect=requests.ConnectionError("down")):
            result = specstream_search.invoke({"query": "anything"})
        self.assertIn("请求失败", result)

    def test_registered_like_the_other_search_tools(self) -> None:
        self.assertIn(specstream_search, AgentTools)
        self.assertIs(WeChatTools["specstream_search"], specstream_search)
        self.assertIs(AgentToolsWithName["specstream_search"], specstream_search)


if __name__ == "__main__":
    unittest.main()
