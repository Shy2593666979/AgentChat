import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from agentchat.core.models.manager import ModelManager
from agentchat.services.mars.ai_news.crawl_news import crawl_today_ai_news, crawl_single_ai_news, \
    sync_crawl_with_selenium
from agentchat.settings import app_settings

NEWS_PROMPT = """
【系统角色】
你是专业的日报生成助手，仅返回 Markdown 文本，禁止任何额外解释。

【任务指令】
1. 根据用户随后提供的原始信息，总结今日工作要点，形成一份详细的日报。
2. 自动提取关键主题，生成形如 `# YYYY-MM-DD AI日报` 的一级标题（日期取今天：{today}）。
3. 正文使用二级及以下标题对内容进行结构化呈现，可包含列表、表格、代码块等 Markdown 元素。
4. 无需寒暄、无需开头结尾说明，直接输出最终 Markdown。

【原始信息】
{news_content}
"""

def yield_message_chunk(message):
    start = 0
    message_length = len(message)
    while start < message_length:
        # 随机生成1-5之间的长度
        chunk_length = random.randint(1, 5)
        # 防止最后一段超出字符串长度
        end = min(start + chunk_length, message_length)
        # 截取片段并返回
        yield message[start:end]
        # 移动起始位置
        start = end

async def crawl_detail_ai_news():
    _, links = crawl_today_ai_news()

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

async def yield_crawl_detail_ai_news(output_detail: bool):
    # loop = asyncio.get_running_loop()
    # with ThreadPoolExecutor(max_workers=1) as executor:
    #     result = await loop.run_in_executor(executor, crawl_today_ai_news, None)

    _, links = sync_crawl_with_selenium(app_settings.default_config.get("mars_daily_url"))

    total_news_content = ""
    # yield {
    #     "type": "event",
    #     "time": time.time(),
    #     "data": {
    #         "title": "抓取AI信息",
    #         "message": "开始抓取网络中有关AI的信息",
    #         "status": "START"
    #     }
    # }
    for idx, link in enumerate(links[:10]):
        title, content = await crawl_single_ai_news(link)
        # 只有用户特地指定了要详细输出才开始输出
        if output_detail:
            yield {
                "type": "tool_chunk",
                "time": time.time(),
                "data": f"\n ## {idx + 1}. [标题：{title}]({link}) \n"
            }

            # 改成流式输出，每次1字符
            for chunk in yield_message_chunk(content):
                yield {
                    "type": "tool_chunk",
                    "time": time.time(),
                    "data": chunk
                }
                await asyncio.sleep(0.02)

        total_news_content += f"\n {idx+1}. 标题：{title}\n内容:{content}\n"

    # yield {
    #     "type": "event",
    #     "time": time.time(),
    #     "data": {
    #         "title": "抓取AI信息",
    #         "message": "开始抓取网络中有关AI的信息",
    #         "status": "END"
    #     }
    # }

    yield {
            "type": "tool_chunk",
            "time": time.time(),
            "data": "### AI新闻已经总结完毕, 接下来我要开始生成一份完整的AI日报内容\n"
        }
    message = NEWS_PROMPT.format(today=date.today(), news_content=total_news_content)

    llm_client = ModelManager.get_conversation_model()

    async for chunk in llm_client.astream(message):
        yield {
            "type": "response_chunk",
            "time": time.time(),
            "data": chunk.content
        }

    yield {
        "type": "final_chunk",
        "time": time.time(),
        "data": total_news_content
    }
