"""Outcrawl 搜索工具的离线测试，使用 mock 替代真实的 HTTP 请求。"""
import asyncio
from unittest.mock import MagicMock, patch

import yaml
from agentchat.schemas.common import Tools
from agentchat.settings import app_settings, init_app_settings, load_settings

asyncio.run(init_app_settings())

from agentchat.tools import AgentToolsWithName, WeChatTools
from agentchat.tools.web_search.outcrawl_search.action import outcrawl_search


def make_response(status_code, payload=None, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.text = text
    return response


def run_search(response, **kwargs):
    tools = Tools(outcrawl={"api_key": "oc-test-key"})
    with patch.object(app_settings, "tools", tools), patch(
        "agentchat.tools.web_search.outcrawl_search.action.requests.post",
        return_value=response,
    ) as post:
        result = outcrawl_search.invoke(kwargs)
    return result, post


def test_registered_like_other_search_tools(tmp_path):
    assert AgentToolsWithName["outcrawl_search"] is outcrawl_search
    assert WeChatTools["outcrawl_search"] is outcrawl_search
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump({"model": {"api_key": "test-only"}}), encoding="utf-8")
    assert load_settings(path).tools.outcrawl["api_key"] == ""


def test_formats_hits_and_sends_request():
    payload = {
        "hits": [
            {"url": "https://example.com/a", "title": "A", "snippet": "first", "rank": 1},
            {"url": "https://example.com/b", "title": "B", "snippet": "second", "rank": 2},
        ],
        "usage": {"credits": "0.5"},
    }
    result, post = run_search(make_response(200, payload), query="agent", count=2)

    assert "引用: 1\n标题: A\nURL: https://example.com/a\n摘要: first" in result
    assert "引用: 2\n标题: B\nURL: https://example.com/b\n摘要: second" in result
    args, kwargs = post.call_args
    assert args[0] == "https://api.outcrawl.ai/v1/search"
    assert kwargs["json"] == {"query": "agent", "limit": 2}
    assert kwargs["headers"]["Authorization"] == "Bearer oc-test-key"


def test_clamps_count():
    _, post = run_search(make_response(200, {"hits": []}), query="agent", count=100)
    assert post.call_args.kwargs["json"]["limit"] == 20
    _, post = run_search(make_response(200, {"hits": []}), query="agent", count=0)
    assert post.call_args.kwargs["json"]["limit"] == 1


def test_empty_and_error_responses():
    result, _ = run_search(make_response(200, {"hits": []}), query="agent")
    assert result == "未找到相关结果。"
    result, _ = run_search(make_response(401, text="invalid key"), query="agent")
    assert result == "搜索API请求失败，状态码: 401, 错误信息: invalid key"
