from langchain.tools import tool
import requests

from agentchat.settings import app_settings


@tool("outcrawl_search", parse_docstring=True)
def outcrawl_search(query: str, count: int = 10) -> str:
    """
    使用 Outcrawl Search API 进行网页搜索。

    Args:
        query (str): 用户的搜索词（必填）
        count (int): 返回结果条数，范围 1-20，默认 10

    Returns:
        str: 格式化的搜索结果或错误信息
    """
    count = min(max(count, 1), 20)
    api_key = app_settings.tools.outcrawl.get("api_key")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AgentChat",
    }

    response = requests.post(
        "https://api.outcrawl.ai/v1/search",
        json={"query": query, "limit": count},
        headers=headers,
        timeout=60,
    )

    if response.status_code == 200:
        try:
            hits = response.json().get("hits") or []
            if not hits:
                return "未找到相关结果。"
            formatted_results = ""
            for idx, item in enumerate(hits[:count], start=1):
                formatted_results += (
                    f"引用: {idx}\n"
                    f"标题: {item.get('title', '')}\n"
                    f"URL: {item.get('url', '')}\n"
                    f"摘要: {item.get('snippet', '')}\n\n"
                )
            return formatted_results.strip()
        except Exception as e:
            return f"搜索API请求失败，原因是：搜索结果解析失败 {str(e)}"
    else:
        return f"搜索API请求失败，状态码: {response.status_code}, 错误信息: {response.text}"
