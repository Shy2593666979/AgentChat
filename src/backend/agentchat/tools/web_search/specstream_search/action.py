from typing import Optional

import requests
from langchain.tools import tool

from agentchat.settings import app_settings

SPECSTREAM_SEARCH_URL = "https://api.specstream.ai/v1/web-search"


def _specstream_search(query: str, max_results: int = 10) -> str:
    """使用 SpecStream Search API 进行网页搜索"""
    api_key = (app_settings.tools.specstream.get("api_key") or "").strip()
    if not api_key:
        return "SpecStream Search API 未配置 api_key（tools.specstream.api_key）"

    params = {"q": query, "num": min(max(max_results, 1), 20)}
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "AgentChat",
    }

    try:
        response = requests.get(SPECSTREAM_SEARCH_URL, headers=headers, params=params, timeout=30)
    except Exception as e:
        return f"SpecStream Search 请求失败: {e}"

    if response.status_code == 401:
        return "SpecStream API Key 无效或已过期"
    if response.status_code == 402:
        return "SpecStream 账户余额不足 (402)"
    if response.status_code == 429:
        return "SpecStream Search 请求频率超限 (429)"
    if response.status_code != 200:
        return f"SpecStream Search 请求失败 (Status {response.status_code})"

    try:
        sources = (response.json().get("data") or {}).get("sources") or []
    except Exception:
        return "SpecStream Search 返回非 JSON 响应"

    if not sources:
        return "未找到相关结果"

    lines = []
    for i, item in enumerate(sources[: params["num"]], 1):
        title = item.get("title") or f"结果 {i}"
        line = f"[{i}] {title}\n   网址: {item.get('url', '')}\n   摘要: {item.get('snippet', '')}"
        if item.get("published"):
            line += f"\n   发布时间: {item['published']}"
        lines.append(line)

    return "\n\n".join(lines)


@tool("specstream_search", parse_docstring=True)
def specstream_search(
    query: str,
    max_results: Optional[int] = 10,
):
    """
    使用 SpecStream Search API 进行联网搜索，每条结果带来源网址和摘要。

    Args:
        query: 用户想要搜索的问题，可以是自然语言
        max_results: 最大返回结果数量，范围 1-20，默认 10

    Returns:
        将联网搜索到的信息格式化后返回给用户
    """
    return _specstream_search(query, max_results=max_results or 10)
