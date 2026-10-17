import asyncio
import json
import time
from datetime import date
from typing import Literal, Optional
from urllib.parse import urljoin

import httpx
from langchain.tools import tool

from agentchat.services.mars.ai_news.report import (
    collect_news,
    create_html_report,
    markdown_report,
    render_report_png,
    summarize_news,
)
from agentchat.services.mars.events import get_mars_writer, progress
from agentchat.services.storage import storage_client
from agentchat.settings import app_settings
from agentchat.utils.file_utils import get_object_storage_base_path
from agentchat.utils.logging import log_event


@tool(parse_docstring=True)
async def crawl_ai_news(
    user_input: str,
    output_format: Literal["markdown", "png"] = "png",
    output_detail: bool = False,
    user_id: Optional[str] = None,
):
    """生成 AI 日报，默认直接展示图文长图，同时提供下载地址。成功后无需重复调用。

    Args:
        user_input: 用户对日报的要求。
        output_format: png 直接展示新闻配图和摘要；markdown 提供文字及文件。
        output_detail: Markdown 是否附上新闻原文，图片始终展示精简摘要。
        user_id: 当前用户ID。

    Returns:
        明确的完成状态、新闻条数和结果地址，图片或正文已经展示给用户。
    """
    writer = get_mars_writer()
    started = time.monotonic()

    def stage(name, since, **fields):
        log_event("mars.news", "日报阶段完成", stage=name,
                  duration_ms=round((time.monotonic() - since) * 1000), **fields)

    writer(progress("并发收集新闻与配图"))
    articles = await collect_news(lambda message: writer(progress(message)))
    stage("collect", started, news_count=len(articles), images=sum(bool(item["image"]) for item in articles))
    writer(progress("整理新闻标题和摘要"))
    tick = time.monotonic()
    articles = await summarize_news(articles, user_input)
    stage("summarize", tick, news_count=len(articles))
    writer({"type": "result_start", "result_key": "ai_news", "data": {}})
    if output_format == "png":
        writer(progress("排版生成图文日报"))
        tick = time.monotonic()
        html = create_html_report(date.today().strftime("%Y年%m月%d日"), articles)
        content = await asyncio.to_thread(render_report_png, html)
        stage("render", tick)
    else:
        content = markdown_report(articles, output_detail)
    name = get_object_storage_base_path(f"ai-daily-{date.today()}.{output_format if output_format == 'png' else 'md'}")
    writer(progress("保存日报文件"))
    tick = time.monotonic()
    await asyncio.to_thread(storage_client.upload_file, name, content)
    url = urljoin(app_settings.storage.active.base_url.rstrip("/") + "/", name)
    # 部分存储适配器仅记录上传异常；确认结果可访问后才向页面发送成功事件。
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.head(url)
        response.raise_for_status()
    stage("upload", tick)
    result = (f"![AI 日报：{len(articles)} 条新闻]({url})\n\n[下载日报原图]({url})"
              if output_format == "png" else content + f"\n\n[下载 Markdown 日报]({url})")
    writer({"type": "tool_chunk", "result_key": "ai_news", "data": result})
    writer(progress("图文日报已生成" if output_format == "png" else "Markdown 日报已生成", "complete"))
    stage("total", started)
    return json.dumps({"status": "completed", "format": output_format, "news_count": len(articles),
                       "url": url, "displayed": True,
                       "message": "日报已生成并展示，任务已完成，请勿再次调用本工具。"}, ensure_ascii=False)
