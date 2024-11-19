import os
from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_community.utilities import SerpAPIWrapper
from config.user_config import userConfig

os.environ["SERPAPI_API_KEY"] = userConfig.TOOL_GOOGLE_API_KEY
search = SerpAPIWrapper()

class GoogleSearchInput(BaseModel):
    query: str = Field(description='用户想要搜索的问题')

class GoogleSearchTool(BaseTool):
    name = 'google_search'
    description = '使用搜索工具给用户进行搜索'
    args_schema: Type[BaseModel] = GoogleSearchInput

    def _run(self, query: str):
        return google_search(query)


def google_search(query: str):
    """使用搜索工具给用户进行搜索"""
    result = search.run(query)
    return result
