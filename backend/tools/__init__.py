from send_email.action import send_email, SendEmailTool
from google_search.action import google_search, GoogleSearchTool
from arxiv.action import get_arxiv, ArxivTool
from get_weather.action import get_weather, WeatherTool
from delivery.action import get_delivery, DeliveryTool
from rag_data.action import exec_rag

action_Function_call = {
    "send_email": send_email,
    "google_search": google_search,
    "get_arxiv": get_arxiv,
    "get_weather": get_weather,
    "get_delivery": get_delivery,
    "RagAgent": exec_rag
}

action_React = {
    "send_email": SendEmailTool,
    "search": GoogleSearchTool,
    "weather": WeatherTool,
    "delivery": DeliveryTool,
    "arxiv": ArxivTool
}
