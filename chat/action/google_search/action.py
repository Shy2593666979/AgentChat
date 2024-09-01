import os
from langchain_community.utilities import SerpAPIWrapper
from config import user_config

os.environ["SERPAPI_API_KEY"] = user_config.TOOL_GOOGLE_API_KEY

def google_search_action(query: str):
    search = SerpAPIWrapper()
    result = search.run(query)

    return result