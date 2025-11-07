from langchain.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from agentchat.settings import app_settings

search = SerpAPIWrapper(serpapi_api_key=app_settings.tools.google.get('api_key'))

@tool("web_search", parse_docstring=True)
def google_search(query: str):
    """
    根据用户的问题进行网上搜索信息。

    Args:
        query (str): 用户的问题。

    Returns:
        str: 搜索到的信息。
    """
    return _google_search(query)

def _google_search(query: str):
    """使用搜索工具给用户进行搜索"""
    result = search.run(query)
    return result
