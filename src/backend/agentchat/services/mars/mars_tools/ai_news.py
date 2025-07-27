import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin
from uuid import uuid4
from loguru import logger

from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.services.mars.ai_news.detial_news import yield_crawl_detail_ai_news
from agentchat.settings import app_settings
from agentchat.utils.file_utils import get_aliyun_oss_base_path


async def crawl_ai_news(user_input: str, user_id: Optional[str] = None):
    """
    帮助用户获取一个AI日报, 而且提供一个可下载的PDF下载链接

    params:
        user_input: 用户输入的问题, 作用不大, 但是是必须的

    return:
        返回来日报内容, 而且包含可下载的pdf链接
    """
    news_response = ""
    async for chunk in yield_crawl_detail_ai_news():
        if chunk.get("type") == "response_chunk":
            news_response += chunk.get("data")
        yield chunk

    yield {
        "type": "tool_chunk",
        "time": time.time(),
        "data": "接下来我要开始生成一份完整的Markdown文件\n"
    }

    try:
        file_name = f"AI日报-{datetime.today()}-{uuid4().hex[:5]}.md"

        oss_object_name = get_aliyun_oss_base_path(file_name)
        sign_url = urljoin(app_settings.aliyun_oss["base_url"], oss_object_name)

        aliyun_oss.sign_url_for_get(sign_url)
        aliyun_oss.upload_file(oss_object_name, news_response)

        yield {
            "type": "tool_chunk",
            "time": time.time(),
            "data": f"文件已经生成完毕, 请点击下载查看 [AI日报]({sign_url})\n"
        }
    except Exception as err:
        logger.error(f"生成日报文件失败:{err}")

