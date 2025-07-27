import asyncio
import time
from datetime import date

from agentchat.core.models.manager import ModelManager
from agentchat.services.mars.ai_news.crawl_news import crawl_today_ai_news, crawl_single_ai_news

NEWS_PROMPT = """
【系统角色】
你是专业的日报生成助手，仅返回 Markdown 文本，禁止任何额外解释。

【任务指令】
1. 根据用户随后提供的原始信息，总结今日工作要点，形成一份日报。
2. 自动提取关键主题，生成形如 `# YYYY-MM-DD AI日报` 的一级标题（日期取今天：{today}）。
3. 正文使用二级及以下标题对内容进行结构化呈现，可包含列表、表格、代码块等 Markdown 元素。
4. 无需寒暄、无需开头结尾说明，直接输出最终 Markdown。

【原始信息】
{news_content}
"""

async def crawl_detail_ai_news():
    _, links = await crawl_today_ai_news()

    total_news_content = ""
    # for link in links[:10]:
    #     title, content = await crawl_single_ai_news(link)
    #     total_news_content += f"\n 标题：{title}\n内容:{content}\n"

    crawl_tasks = []
    for link in links[:10]:
        crawl_tasks.append(crawl_single_ai_news(link))

    results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
    for title, content in results:
        total_news_content += f"\n 标题：{title}\n内容:{content}\n"

    message = NEWS_PROMPT.format(today=date.today(), news_content=total_news_content)

    llm_client = ModelManager.get_conversation_model()

    response = await llm_client.ainvoke(message)

    return response

async def yield_crawl_detail_ai_news():
    _, links = await crawl_today_ai_news()

    total_news_content = ""
    yield {
        "type": "event",
        "time": time.time(),
        "data": {
            "title": "抓取AI信息",
            "message": "开始抓取网络中有关AI的信息",
            "status": "START"
        }
    }
    for link in links[:10]:
        title, content = await crawl_single_ai_news(link)
        yield {
            "type": "tool_chunk",
            "time": time.time(),
            "data": f"\n 标题：{title}\n内容:{content[:100]}...\n"
        }
        total_news_content += f"\n 标题：{title}\n内容:{content}\n"

    yield {
        "type": "event",
        "time": time.time(),
        "data": {
            "title": "抓取AI信息",
            "message": "开始抓取网络中有关AI的信息",
            "status": "END"
        }
    }

    yield {
            "type": "tool_chunk",
            "time": time.time(),
            "data": "\nAI信息已经抓取完毕, 接下来我要开始生成一份完整的AI日报内容\n"
        }
    message = NEWS_PROMPT.format(today=date.today(), news_content=total_news_content)

    llm_client = ModelManager.get_conversation_model()

    async for chunk in llm_client.astream(message):
        yield {
            "type": "response_chunk",
            "time": time.time(),
            "data": chunk.content
        }