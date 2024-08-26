import os
from langchain_community.utilities import SerpAPIWrapper
from config.tool_config import SERPAPI_API_KEY

os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY

def google_search_action(query: str):
    search = SerpAPIWrapper()
    result = search.run(query)

    return result