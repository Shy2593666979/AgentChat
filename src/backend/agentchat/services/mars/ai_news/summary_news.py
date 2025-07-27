import asyncio
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

async def crawl_summary_ai_news():
    total_news_content, _ = await crawl_today_ai_news()

    message = NEWS_PROMPT.format(today=date.today(), news_content=total_news_content)

    llm_client = ModelManager.get_conversation_model()
    response = await llm_client.ainvoke(message)

    return response