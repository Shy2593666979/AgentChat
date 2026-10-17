"""日报只整理一次，抓取有并发上限，结果以可展示图片返回。"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from agentchat.settings import app_settings, init_app_settings

asyncio.run(init_app_settings())
app_settings.database = {"url": "sqlite:///:memory:"}

from agentchat.services.mars.ai_news import report
from agentchat.services.mars.mars_tools import ai_news


def article(index=1):
    return {"title": f"新闻标题{index}", "content": "原始新闻正文", "description": "这是一条新闻摘要。",
            "url": f"https://news.example/zh/news/{index}", "image": "", "image_url": ""}


def test_collection_is_bounded_concurrent_and_tolerates_article_failure(monkeypatch):
    monkeypatch.setattr(app_settings, "default_config", {"mars_daily_url": "https://news.example/zh/news"})
    active = peak = 0

    async def transport(request):
        nonlocal active, peak
        if request.url.path == "/zh/news":
            return httpx.Response(200, text="".join(f'<a href="/zh/news/{n}">新闻{n}</a>' for n in range(8)))
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(0.01)
            if request.url.path.endswith("/3"):
                raise httpx.ReadTimeout("one article timed out")
            return httpx.Response(200, text="<h1>标题</h1><article><p>新闻正文</p></article>")
        finally:
            active -= 1

    async def check():
        events = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            articles = await report.collect_news(events.append, client=client)
        assert len(articles) == 7
        assert 2 <= peak <= report.CONCURRENCY
        assert len(events) == 8
    asyncio.run(check())


def test_thumbnail_failure_keeps_article(monkeypatch):
    monkeypatch.setattr(app_settings, "default_config", {"mars_daily_url": "https://news.example/zh/news"})

    async def transport(request):
        if request.url.path == "/zh/news":
            return httpx.Response(200, text='<a href="/zh/news/1">新闻</a>')
        if request.url.path.endswith(".png"):
            raise httpx.ReadTimeout("image timed out")
        return httpx.Response(200, text='<meta property="og:image" content="/image.png"><h1>标题</h1><article><p>正文</p></article>')

    async def check():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            articles = await report.collect_news(lambda message: None, client=client)
        assert len(articles) == 1 and articles[0]["image"] == ""
    asyncio.run(check())


def test_summary_uses_one_bounded_non_thinking_model_call(monkeypatch):
    model = Mock()
    model.bind.return_value = model
    model.ainvoke = AsyncMock(return_value=SimpleNamespace(content=json.dumps({"items": [
        {"index": 2, "title": "第二条", "description": "摘要二"},
        {"index": 1, "title": "第一条", "description": "摘要一"},
    ]})))
    monkeypatch.setattr(report.ModelManager, "get_chat_model", lambda: model)
    monkeypatch.setattr(app_settings, "multi_models", SimpleNamespace(chat_model=SimpleNamespace(model_name="qwen3.8-flash")))
    items = asyncio.run(report.summarize_news([article(1), article(2)]))
    assert [item["title"] for item in items] == ["第一条", "第二条"]
    assert items[0]["url"] == article(1)["url"]
    model.ainvoke.assert_awaited_once()
    assert model.bind.call_args.kwargs == {"max_tokens": 2400, "extra_body": {"enable_thinking": False},
                                           "response_format": {"type": "json_object"}}


def test_report_escapes_source_text_and_uses_embedded_images():
    html = report.create_html_report("2026-10-17", [
        {**article(), "title": '<script>alert(1)</script>', "image": "data:image/png;base64,aGVsbG8="},
        article(2),
    ])
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert '<img src="data:image/png;base64,' in html
    assert 'class="placeholder"' in html
    assert "新闻标题2" in html


def test_nuxt_article_uses_own_body_and_thumbnail():
    values = [{"getAIDetail": 1}, {"data": 2}, {"title": 3, "summary": 4, "thumb": 5},
              "当前新闻", "<p>真实正文</p>", "https://files.example/news.jpg"]
    html = '<h1>当前新闻</h1><article><p>不相关的推荐新闻</p></article>' + \
        '<script id="__NUXT_DATA__" type="application/json">' + json.dumps(values) + '</script>'
    item = report.parse_article(html, "https://news.example/zh/news/1")
    assert item["content"] == "真实正文"
    assert item["image_url"] == "https://files.example/news.jpg"


def test_long_summary_is_shortened_locally():
    item = report.NewsSummary(index=1, title="标题" * 30, description="摘要" * 80)
    assert len(item.title) == 28
    assert len(item.description) == 100
    sentence = "这条新闻的主要事实已经完整说明。" * 3
    item = report.NewsSummary(index=1, title="标题", description=sentence + "很长的附加说明" * 30)
    assert item.description.endswith("。")
    assert len(item.description) <= 100


@pytest.mark.parametrize("output_format", ["png", "markdown"])
def test_tool_returns_completion_and_displays_image_or_markdown(monkeypatch, output_format):
    emitted = []
    stored = {}
    monkeypatch.setattr(ai_news, "get_mars_writer", lambda: emitted.append)
    monkeypatch.setattr(ai_news, "collect_news", AsyncMock(return_value=[article()]))
    summary = AsyncMock(return_value=[article()])
    monkeypatch.setattr(ai_news, "summarize_news", summary)
    monkeypatch.setattr(ai_news, "render_report_png", lambda html: b"PNG bytes")
    monkeypatch.setattr(ai_news, "get_object_storage_base_path", lambda name: "daily/report." + ("png" if output_format == "png" else "md"))
    monkeypatch.setattr(ai_news, "storage_client", SimpleNamespace(upload_file=lambda name, content: stored.update({name: content})))
    monkeypatch.setattr(app_settings, "storage", SimpleNamespace(active=SimpleNamespace(base_url="https://files.example/")))
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200)))
    monkeypatch.setattr(ai_news.httpx, "AsyncClient", lambda **kwargs: client)
    result = json.loads(asyncio.run(ai_news.crawl_ai_news.coroutine(user_input="今天的日报", output_format=output_format)))
    assert result["status"] == "completed" and result["displayed"] is True
    assert result["url"].startswith("https://files.example/daily/report.")
    summary.assert_awaited_once()
    output = [event["data"] for event in emitted if event["type"] == "tool_chunk"]
    assert len(output) == 1
    if output_format == "png":
        assert output[0].startswith("![AI 日报")
        assert result["url"] in output[0] and stored["daily/report.png"] == b"PNG bytes"
    else:
        assert "# " in output[0] and "新闻来源" in output[0]


def test_upload_error_is_not_reported_as_success(monkeypatch):
    emitted = []
    monkeypatch.setattr(ai_news, "get_mars_writer", lambda: emitted.append)
    monkeypatch.setattr(ai_news, "collect_news", AsyncMock(return_value=[article()]))
    monkeypatch.setattr(ai_news, "summarize_news", AsyncMock(return_value=[article()]))
    monkeypatch.setattr(ai_news, "render_report_png", lambda html: b"PNG bytes")
    def fail(*args):
        raise OSError("upload failed")
    monkeypatch.setattr(ai_news, "storage_client", SimpleNamespace(upload_file=fail))
    with pytest.raises(OSError):
        asyncio.run(ai_news.crawl_ai_news.coroutine(user_input="日报"))
    assert not any(event["type"] == "tool_chunk" for event in emitted)


def test_missing_uploaded_file_does_not_emit_picture(monkeypatch):
    emitted = []
    monkeypatch.setattr(ai_news, "get_mars_writer", lambda: emitted.append)
    monkeypatch.setattr(ai_news, "collect_news", AsyncMock(return_value=[article()]))
    monkeypatch.setattr(ai_news, "summarize_news", AsyncMock(return_value=[article()]))
    monkeypatch.setattr(ai_news, "render_report_png", lambda html: b"PNG bytes")
    monkeypatch.setattr(ai_news, "storage_client", SimpleNamespace(upload_file=lambda *args: None))
    monkeypatch.setattr(app_settings, "storage", SimpleNamespace(active=SimpleNamespace(base_url="https://files.example/")))
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(404)))
    monkeypatch.setattr(ai_news.httpx, "AsyncClient", lambda **kwargs: client)
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(ai_news.crawl_ai_news.coroutine(user_input="日报"))
    assert not any(event["type"] == "tool_chunk" for event in emitted)
