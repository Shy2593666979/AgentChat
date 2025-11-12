from agentchat.services.mars.mars_tools.ai_news import crawl_ai_news
from agentchat.services.mars.mars_tools.autobuild import auto_build_agent
from agentchat.services.mars.mars_tools.query_knowledge import query_knowledge
from agentchat.services.mars.mars_tools.deepsearch import deep_search

MarsTool = {
    "crawl_ai_news": crawl_ai_news,
    "auto_build_agent": auto_build_agent,
    "query_knowledge": query_knowledge,
    "deep_search": deep_search,
}