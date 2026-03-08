import json
import os
import time
from datetime import datetime
from typing import Optional, Literal
from urllib.parse import urljoin
from loguru import logger
from html2image import Html2Image
from langchain.tools import tool
from langgraph.config import get_stream_writer
from agentchat.core.models.manager import ModelManager
from agentchat.services.storage import storage_client
from agentchat.services.mars.ai_news.detial_news import yield_crawl_detail_ai_news
from agentchat.services.mars.ai_news.prompt import GENERATE_JSON_NEWS, FIX_JSON_PROMPT
from agentchat.utils.file_utils import get_object_storage_base_path, get_save_tempfile
from agentchat.settings import app_settings


@tool(parse_docstring=True)
async def crawl_ai_news(
    user_input: str,
    output_format: Literal["markdown", "png"] = "png",
    output_detail: bool = False,
    user_id: Optional[str] = None
):
    """
    帮助用户获取一个AI日报, 如果用户有需求，可以提供一个可下载的Markdown下载链接

    Args:
        user_input: 用户输入的问题
        output_format: 给用户提供的日报下载文件格式，包含markdown和图片png两种，默认是png
        output_detail: 是否需要给用户提供详细的日报内容
        user_id: 当前用户ID，默认为None

    Returns:
        返回来日报内容, 根据用户的需求判断是否包含可下载的Markdown链接
    """
    writer = get_stream_writer()

    news_response = ""
    final_response = ""
    async for chunk in yield_crawl_detail_ai_news(output_detail):
        if chunk.get("type") == "response_chunk":
            news_response += chunk.get("data")
        if chunk.get("type") == "final_chunk":
            final_response = chunk.get("data")
            continue
        writer(chunk)

    if output_format == "markdown":
        writer({
            "type": "tool_chunk",
            "time": time.time(),
            "data": "\n\n接下来我要开始生成一份完整的Markdown文件\n"
        })

        try:
            file_name = f"AI日报-{datetime.today().date()}.md"

            oss_object_name = get_object_storage_base_path(file_name)
            sign_url = urljoin(app_settings.storage.active.base_url, oss_object_name)

            storage_client.sign_url_for_get(sign_url)
            storage_client.upload_file(oss_object_name, news_response)

            writer({
                "type": "tool_chunk",
                "time": time.time(),
                "data": f"\n\n文件已经生成完毕, 请点击下载查看 [AI日报📰]({sign_url}) \n"
            })
        except Exception as err:
            logger.error(f"生成日报文件失败:{err}")

    else:
        sample_date = datetime.today().strftime("%Y年%m月%d日")
        conversation_model = ModelManager.get_conversation_model()

        response = await conversation_model.ainvoke(GENERATE_JSON_NEWS.format(news_content=final_response))
        # 默认值
        sample_content = []
        try:
            response.content = response.content.replace("```json", "").replace("```", "")
            sample_content = json.loads(response.content)
        except Exception as err:
            logger.error(f"生成Json格式的新闻简述，我将开始修复这个Json格式的数据: {response.content}")
            fix_response = await conversation_model.ainvoke(FIX_JSON_PROMPT.format(json_error=str(err), json_content=response.content))
            try:
                sample_content = json.loads(fix_response.content)
            except Exception as err:
                logger.error("无法修复改Json格式的新闻简述，建议更换模型再来试试~")
                raise

        html_content = create_html_report(sample_date, sample_content)
        hti = Html2Image(
            custom_flags=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',  # 禁用 GPU
                '--disable-dev-shm-usage',  # 避免共享内存不足
                '--no-zygote',  # 配合 --no-sandbox 使用
            ]
        )

        png_save_name = f'{sample_date}.png'

        hti.screenshot(html_str=html_content, save_as=png_save_name, size=(650, 2100))

        png_file_content = ""
        with open(png_save_name, 'rb') as file:
            png_file_content = file.read()

        oss_object_name = get_object_storage_base_path(png_save_name)
        sign_url = urljoin(app_settings.storage.active.base_url, oss_object_name)

        storage_client.sign_url_for_get(sign_url)
        storage_client.upload_file(oss_object_name, png_file_content)
        # 在本地进行删除
        os.remove(png_save_name)

        writer({
            "type": "tool_chunk",
            "time": time.time(),
            "data": "\n ### 图片已经生成完毕, 请点击或下载查看✅ \n"
        })
        writer({
            "type": "tool_chunk",
            "time": time.time(),
            "data": f"![AI日报]({sign_url}) \n"
        })


def get_html_template():
    """返回HTML模板，避免格式化冲突"""
    return """
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AI资讯简报</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
            
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
                        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                        padding: 0;
                        margin: 0;
                    }}
            
                    .news-report {{
                        width: 600px;
                        min-height: 800px;
                        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                        margin: 0;
                        padding: 50px 40px;
                        position: relative;
                        overflow: hidden;
                    }}
            
                    .news-report::before {{
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 5px;
                        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
                    }}
            
                    .report-header {{
                        text-align: center;
                        margin-bottom: 50px;
                    }}
            
                    .report-title {{
                        font-size: 48px;
                        font-weight: 900;
                        color: #1e3a8a;
                        margin-bottom: 15px;
                        letter-spacing: 3px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                    }}
            
                    .report-date {{
                        font-size: 20px;
                        color: #64748b;
                        margin-bottom: 25px;
                        font-weight: 500;
                    }}
            
                    .report-divider {{
                        width: 150px;
                        height: 4px;
                        background: linear-gradient(90deg, #667eea, #764ba2);
                        margin: 0 auto;
                        border-radius: 2px;
                        position: relative;
                    }}
            
                    .report-divider::after {{
                        content: '';
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 12px;
                        height: 12px;
                        background: #6366f1;
                        border-radius: 50%;
                        border: 4px solid #f8fafc;
                    }}
            
                    .report-news-list {{
                        margin-top: 50px;
                    }}
            
                    .report-news-item {{
                        display: flex;
                        margin-bottom: 30px;
                        position: relative;
                        align-items: flex-start;
                    }}
            
                    .report-news-number {{
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        color: white;
                        font-size: 16px;
                        margin-right: 20px;
                        flex-shrink: 0;
                        box-shadow: 0 6px 15px rgba(0,0,0,0.2);
                        z-index: 2;
                    }}
            
                    .report-news-line {{
                        position: absolute;
                        left: 19px;
                        top: 40px;
                        bottom: -15px;
                        width: 3px;
                        background: linear-gradient(to bottom, transparent 0%, currentColor 15%, currentColor 85%, transparent 100%);
                        z-index: 1;
                    }}
            
                    .report-news-item:last-child .report-news-line {{
                        display: none;
                    }}
            
                    .report-news-content {{
                        flex: 1;
                        background: white;
                        padding: 25px;
                        border-radius: 18px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        border: 1px solid #e5e7eb;
                        position: relative;
                        transition: all 0.3s ease;
                        margin-top: -5px;
                    }}
            
                    .report-news-content::before {{
                        content: '';
                        position: absolute;
                        left: -8px;
                        top: 20px;
                        width: 0;
                        height: 0;
                        border-top: 8px solid transparent;
                        border-bottom: 8px solid transparent;
                        border-right: 8px solid white;
                    }}
            
                    .report-news-title {{
                        font-size: 17px;
                        font-weight: 700;
                        color: #1f2937;
                        line-height: 1.5;
                        margin-bottom: 12px;
                    }}
            
                    .report-news-desc {{
                        font-size: 14px;
                        color: #6b7280;
                        line-height: 1.6;
                    }}
            
                    .report-news-category {{
                        position: absolute;
                        top: -10px;
                        right: 20px;
                        padding: 6px 16px;
                        border-radius: 15px;
                        font-size: 12px;
                        font-weight: 700;
                        color: white;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    }}
            
                    .category-技术, .tech {{ 
                        background: linear-gradient(135deg, #6366f1, #8b5cf6); 
                        color: #6366f1;
                    }}
                    .category-产品, .product {{ 
                        background: linear-gradient(135deg, #3b82f6, #1d4ed8); 
                        color: #3b82f6;
                    }}
                    .category-资讯, .news {{ 
                        background: linear-gradient(135deg, #8b5cf6, #a855f7); 
                        color: #8b5cf6;
                    }}
            
                    .report-footer {{
                        margin-top: 60px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
            
                    .report-quote {{
                        background: white;
                        padding: 15px 25px;
                        border-radius: 25px;
                        font-size: 15px;
                        color: #374151;
                        border: 2px solid #374151;
                        font-style: italic;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                        text-align: center; /* 内部文本居中 */
                        margin: 0 auto; /* 元素自身在父容器中水平居中 */
                        max-width: fit-content; /* 让元素宽度适应内容，避免过度拉伸 */
                    }}
            
                    .report-info {{
                        background: #1e293b;
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        color: white;
                        min-width: 120px;
                        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                    }}
            
                    .report-info-title {{
                        font-size: 14px;
                        font-weight: 700;
                        margin-bottom: 5px;
                    }}
            
                    .report-info-subtitle {{
                        font-size: 11px;
                        color: #94a3b8;
                        line-height: 1.3;
                    }}
            
                    .qr-placeholder {{
                        width: 50px;
                        height: 50px;
                        background: white;
                        border: 2px solid #374151;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 10px;
                        color: #374151;
                        font-weight: bold;
                        margin-top: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="news-report">
                    <div class="report-header">
                        <h1 class="report-title">AI资讯简报</h1>
                        <div class="report-date">{date}</div>
                        <div class="report-divider"></div>
                    </div>
            
                    <div class="report-news-list">
                        {news_items}
                    </div>
            
                    <div class="report-footer">
                        <div class="report-quote">由www.agentchat.cloud提供</div>
                    </div>
                </div>
            </body>
            </html>
"""


def generate_news_item_html(index, title, description):
    """生成单个新闻条目的HTML"""
    color = '#6366f1'

    return f"""
            <div class="report-news-item">
                <div class="report-news-number" style="background: {color};">{index}</div>
                <div class="report-news-line" style="color: {color};"></div>
                <div class="report-news-content">
                    <div class="report-news-title">{title}</div>
                    <div class="report-news-desc">{description}</div>
                </div>
            </div>
    """


def create_html_report(date, news_data):
    """创建完整的HTML报告"""
    news_items_html = ""
    for i, item in enumerate(news_data, 1):
        news_items_html += generate_news_item_html(
            i,
            item['title'],
            item['description'],
        )

    template = get_html_template()
    return template.format(
        date=date,
        news_items=news_items_html
    )


# 使用示例
def main():
    # 示例数据
    sample_date = "2025年08月14日"
    sample_news = [
        {
            "title": "我国人工智能专利数占全球 60%",
            "description": "鸿蒙系统生态设备总量突破 11.9 亿台，显示我国在AI技术领域的快速发展和广泛应用。",
            "category": "技术"
        },
        {
            "title": "Siri 迎来最大改造",
            "description": "消息称苹果启动 AI 双轨计划，同步推进自研和外援，提升语音助手的智能化水平。",
            "category": "产品"
        },
        {
            "title": "苹果展示 AI 新成果",
            "description": "在 Siri 延迟中突围，用户数据隐私始终放在首位，展现负责任的AI发展理念。",
            "category": "技术"
        },
        {
            "title": "中文数据训练成主流",
            "description": "我国多数模型使用的中文数据占比超过 60%，部分高达 80%，本土化程度不断提升。",
            "category": "技术"
        },
        {
            "title": "Windows 未来界面大变革",
            "description": "微软高管畅想 Windows 未来，AI 将能读懂用户屏幕，实现更智能的人机交互。",
            "category": "资讯"
        },
        {
            "title": "我国人工智能专利数占全球 60%",
            "description": "鸿蒙系统生态设备总量突破 11.9 亿台，显示我国在AI技术领域的快速发展和广泛应用。",
            "category": "技术"
        },
        {
            "title": "Siri 迎来最大改造",
            "description": "消息称苹果启动 AI 双轨计划，同步推进自研和外援，提升语音助手的智能化水平。",
            "category": "产品"
        },
        {
            "title": "苹果展示 AI 新成果",
            "description": "在 Siri 延迟中突围，用户数据隐私始终放在首位，展现负责任的AI发展理念。",
            "category": "技术"
        },
        {
            "title": "中文数据训练成主流",
            "description": "我国多数模型使用的中文数据占比超过 60%，部分高达 80%，本土化程度不断提升。",
            "category": "技术"
        },
        {
            "title": "Windows 未来界面大变革",
            "description": "微软高管畅想 Windows 未来，AI 将能读懂用户屏幕，实现更智能的人机交互。",
            "category": "资讯"
        }
    ]

    # 生成HTML
    html_content = create_html_report(sample_date, sample_news)


    hti = Html2Image()
    hti.screenshot(html_str=html_content, save_as='测试.png', size= (650,2500))


if __name__ == "__main__":
    main()
