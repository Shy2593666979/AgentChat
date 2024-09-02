import os
from langchain_community.utilities import SerpAPIWrapper
from config.user_config import userConfig

os.environ["SERPAPI_API_KEY"] = userConfig.TOOL_GOOGLE_API_KEY

def google_search_action(query: str):
    search = SerpAPIWrapper()
    result = search.run(query)

    return result