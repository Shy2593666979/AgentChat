from agentchat.tools.send_email.action import send_email, SendEmailTool
from agentchat.tools.web_search.google_search.action import google_search, GoogleSearchTool
from agentchat.tools.web_search.tavily_search.action import tavily_search, TavilySearchTool
from agentchat.tools.arxiv.action import get_arxiv, ArxivTool
from agentchat.tools.get_weather.action import get_weather, WeatherTool
from agentchat.tools.delivery.action import get_delivery, DeliveryTool
from agentchat.tools.text2image.action import text_to_image, Text2ImageTool
# from agentchat.tools.crawl_web.action import crawl_web, CrawlWebTool
from agentchat.tools.convert_to_pdf.action import convert_to_pdf, ConvertPdfTool
from agentchat.tools.convert_to_docx.action import convert_to_docx, ConvertDocxTool
from agentchat.tools.image2text.action import image_to_text, Image2TextTool


LingSeekPlugins = {
    "send_email": send_email,
    "tavily_search": tavily_search,
    "get_arxiv": get_arxiv,
    "get_weather": get_weather,
    "get_delivery": get_delivery,
    "text_to_image": text_to_image,
    "image_to_text": image_to_text,
    "convert_to_pdf": convert_to_pdf,
    "convert_to_docx": convert_to_docx,
}

action_Function_call = {
    "send_email": send_email,
    # "google_search": google_search,
    "tavily_search": tavily_search,
    "get_arxiv": get_arxiv,
    "get_weather": get_weather,
    "get_delivery": get_delivery,
    # "crawl_web": crawl_web,
    "text_to_image": text_to_image,
    "convert_to_pdf": convert_to_pdf,
    "convert_to_docx": convert_to_docx,
    # "RagAgent": exec_rag
}

Call_Tool = {
    "send_email": send_email,
    # "google_search": google_search,
    "tavily_search": tavily_search,
    "get_arxiv": get_arxiv,
    "get_weather": get_weather,
    "get_delivery": get_delivery,
    # "crawl_web": crawl_web,
    "text_to_image": text_to_image,
    "image_to_text": image_to_text,
    "convert_to_pdf": convert_to_pdf,
    "convert_to_docx": convert_to_docx,
}

action_React = {
    "send_email": SendEmailTool,
    # "google_search": GoogleSearchTool,
    "tavily_search": TavilySearchTool,
    "get_weather": WeatherTool,
    "get_delivery": DeliveryTool,
    "get_arxiv": ArxivTool,
    "convert_to_pdf": ConvertPdfTool,
    "convert_to_docx": ConvertDocxTool,
    "text_to_image": Text2ImageTool
    # "crawl_web": CrawlWebTool
}
