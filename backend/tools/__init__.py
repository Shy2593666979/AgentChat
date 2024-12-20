from tools.send_email.action import send_email, SendEmailTool
from tools.google_search.action import google_search, GoogleSearchTool
from tools.arxiv.action import get_arxiv, ArxivTool
from tools.get_weather.action import get_weather, WeatherTool
from tools.delivery.action import get_delivery, DeliveryTool
from tools.crawl_web.action import crawl_web, CrawlWebTool
from tools.rag_data.action import exec_rag

action_Function_call = {
    "send_email": send_email,
    "google_search": google_search,
    "get_arxiv": get_arxiv,
    "get_weather": get_weather,
    "get_delivery": get_delivery,
    "crawl_web": crawl_web,
    "RagAgent": exec_rag
}

action_React = {
    "send_email": SendEmailTool,
    "google_search": GoogleSearchTool,
    "get_weather": WeatherTool,
    "get_delivery": DeliveryTool,
    "get_arxiv": ArxivTool,
    "crawl_web": CrawlWebTool
}
