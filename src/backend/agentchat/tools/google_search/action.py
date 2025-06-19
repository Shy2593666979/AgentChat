import os
from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from agentchat.settings import app_settings
from langchain_community.utilities import SerpAPIWrapper

# os['SERPAPI_API_KEY`'] =
search = SerpAPIWrapper(serpapi_api_key=app_settings.tool_google.get('api_key'))

class GoogleSearchInput(BaseModel):
    query: str = Field(description='用户想要搜索的问题')

class GoogleSearchTool(BaseTool):
    name: str = 'google_search'
    description: str = '使用搜索工具给用户进行搜索'
    args_schema: Type[BaseModel] = GoogleSearchInput

    def _run(self, query: str):
        return google_search(query)


def google_search(query: str):
    """使用搜索工具给用户进行搜索"""
    result = search.run(query)
    return result
