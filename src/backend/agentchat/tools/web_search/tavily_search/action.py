import os
from typing import Type, Optional, Literal
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, validate_call
from agentchat.settings import app_settings
from tavily import TavilyClient

tavily_client = TavilyClient(app_settings.tools.tavily.get("api_key"))


class TavilySearchInput(BaseModel):
    query: str = Field(description='用户想要搜索的问题')
    topic: Optional[Literal["general", "news", "finance"]] = Field(
        None,
        description='搜索主题领域，general为通用，news为新闻，finance为财经'
    )
    time_range: Optional[Literal["day", "week", "month", "year"]] = Field(
        None,
        description='时间范围，筛选过去一天、一周、一个月或一年的内容'
    )
    start_date: Optional[str] = Field(
        None,
        description='起始日期，格式为YYYY-MM-DD，用于精确时间范围筛选'
    )
    end_date: Optional[str] = Field(
        None,
        description='结束日期，格式为YYYY-MM-DD，用于精确时间范围筛选'
    )
    days: Optional[int] = Field(
        None,
        description='过去N天，用于指定最近N天内的内容'
    )
    max_results: Optional[int] = Field(
        None,
        ge=3,  # 最小值3
        le=10,  # 最大值10
        description='最大返回结果数量，控制结果数量上限',
    )


class TavilySearchTool(BaseTool):
    name: str = 'tavily_search'
    description: str = '使用搜索工具给用户进行搜索'
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(self, query: str):
        return tavily_search(query)

@validate_call
def tavily_search(query: str, max_results: Optional[int]=None):
    """使用Tavily搜索工具给用户进行搜索"""
    response = tavily_client.search(
        query=query,
        country="china",
        max_results=max_results
    )

    return "\n\n".join([f'网址:{result["url"]}, 内容: {result["content"]}' for result in response["results"]])

# query: str = Field(description='用户想要搜索的问题'),
# topic: Optional[Literal["general", "news", "finance"]] = Field(
#     None,
#     description='搜索主题领域，general为通用，news为新闻，finance为财经'
# ),
# time_range: Optional[Literal["day", "week", "month", "year"]] = Field(
#     None,
#     description='时间范围，筛选过去一天、一周、一个月或一年的内容'
# ),
# start_date: Optional[str] = Field(
#     None,
#     description='起始日期，格式为YYYY-MM-DD，用于精确时间范围筛选'
# ),
# end_date: Optional[str] = Field(
#     None,
#     description='结束日期，格式为YYYY-MM-DD，用于精确时间范围筛选'
# ),
# days: Optional[int] = Field(
#     None,
#     description='过去N天，用于指定最近N天内的内容'
# ),
# max_results: Optional[int] = Field(
#     None,
#     ge=3,  # 最小值3
#     le=10,  # 最大值10
#     description='最大返回结果数量，控制结果数量上限',
# )):