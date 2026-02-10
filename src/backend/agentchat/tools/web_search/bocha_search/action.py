from langchain.tools import tool
import requests
from typing import Optional, Literal

from agentchat.settings import app_settings

# 定义 freshness 的合法值（提升类型安全性）
FreshnessType = Literal[
    "noLimit", "oneDay", "oneWeek", "oneMonth", "oneYear"
]

@tool("bocha_search", parse_docstring=True)
def bocha_search(
    query: str,
    count: int = 10,
    freshness: FreshnessType = "noLimit",
    summary: bool = True,
    include: Optional[str] = None,
    exclude: Optional[str] = None
) -> str:
    """
    使用 Bocha Web Search API 进行网页搜索。

    Args:
        query (str): 用户的搜索词（必填）
        count (int): 返回结果条数，范围 1-50，默认 10
        freshness (str): 时间范围，默认 "noLimit" 可选: "noLimit", "oneDay", "oneWeek", "oneMonth", "oneYear" 也支持自定义日期格式如 "2025-01-01..2025-04-06" 或 "2025-04-06"
        summary (bool): 是否返回文本摘要，默认 False（与 API 默认一致）
        include (str, optional): 限定搜索的网站域名，多个用 | 或 , 分隔（≤100个）
        exclude (str, optional): 排除的网站域名，多个用 | 或 , 分隔（≤100个）

    Returns:
        str: 格式化的搜索结果或错误信息
    """

    url = app_settings.tools.bocha.get("url")
    headers = {
        'Authorization': f'Bearer {app_settings.tools.bocha.get("api_key")}',  # 请替换为你的API密钥
        # 'Authorization': f'Bearer sk-**************',  # 请替换为你的API密钥
        'Content-Type': 'application/json'
    }
    # 构建请求体（只包含非 None 值）
    data = {
        "query": query,
        "count": min(max(count, 1), 50),  # 确保在 1-50 范围内
    }

    # 可选参数：仅当用户显式传入时才添加
    if freshness != "noLimit":
        data["freshness"] = freshness
    if summary:
        data["summary"] = True
    if include is not None:
        data["include"] = include
    if exclude is not None:
        data["exclude"] = exclude

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        json_response = response.json()
        try:
            if json_response["code"] != 200 or not json_response["data"]:
                return f"搜索API请求失败，原因是: {response.msg or '未知错误'}"

            webpages = json_response["data"]["webPages"]["value"]
            print(webpages)
            if not webpages:
                return "未找到相关结果。"
            formatted_results = ""
            for idx, page in enumerate(webpages, start=1):
                formatted_results += (
                    f"引用: {idx}\n"
                    f"标题: {page['name']}\n"
                    f"URL: {page['url']}\n"
                    f"摘要: {page['summary']}\n"
                    f"网站名称: {page['siteName']}\n"
                    f"网站图标: {page['siteIcon']}\n"
                    f"发布时间: {page['dateLastCrawled']}\n\n"
                )
            return formatted_results.strip()
        except Exception as e:
            return f"搜索API请求失败，原因是：搜索结果解析失败 {str(e)}"
    else:
        return f"搜索API请求失败，状态码: {response.status_code}, 错误信息: {response.text}"