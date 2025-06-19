import asyncio
from typing import Type, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler

class CrawlWebInput(BaseModel):
    web_url: str = Field(description='想要爬取内容的网页地址')

class CrawlWebTool(BaseTool):
    name: str = 'crawl_web'
    description: str = '帮助用户爬取网页的内容信息'
    args_schema: Type[BaseModel] = CrawlWebInput

    def _run(self, web_url: str):
        return crawl_web(web_url)

def crawl_web(web_url: str):
    """帮助用户爬取网页的内容信息"""
    result = asyncio.run(crawl_action(web_url))
    return result

async def crawl_action(web_url: str):
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=web_url)
        return result.markdown

