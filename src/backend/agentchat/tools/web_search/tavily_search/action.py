from typing import Literal, Optional, Type

from langchain.tools import tool
from tavily import TavilyClient

from agentchat.settings import app_settings


@tool("web_search", parse_docstring=True)
def tavily_search(query: str,
                  topic: Optional[str],
                  max_results: Optional[int],
                  time_range: Optional[Literal["day", "week", "month", "year"]]):
    """
    根据用户的问题以及查询参数进行联网搜索

    Args:
        query: 用户想要搜索的问题
        topic: 搜索主题领域，general为通用，news为新闻，finance为财经
        max_results: 最大返回结果数量，控制结果数量上限
        time_range: 时间范围，筛选过去一天、一周、一个月或一年的内容

    Returns:
        将联网搜索到的信息返回给用户
    """
    return _tavily_search(query, topic, max_results, time_range)

def _tavily_search(query, topic, max_results, time_range):
    """使用Tavily搜索工具给用户进行搜索"""
    api_key = app_settings.tools.tavily.get("api_key")
    if not api_key:
        return "当前未启用 Tavily 搜索服务"
    tavily_client = TavilyClient(api_key=api_key)
    response = tavily_client.search(
        query=query,
        country="china",
        topic=topic,
        time_range=time_range,
        max_results=max_results
    )

    return "\n\n".join([f'网址:{result["url"]}, 内容: {result["content"]}' for result in response["results"]])
