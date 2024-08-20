import os
from langchain.utilities import SerpAPIWrapper

os.environ["SERPAPI_API_KEY"] = "cdc3b207606843b4c883849c3a0f833c13057811bea964bef192707d8845f3d8"

def google_search_action(query: str):
    search = SerpAPIWrapper()
    result = search.run(query)

    return result