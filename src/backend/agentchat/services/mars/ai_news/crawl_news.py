from loguru import logger
from requests_html import HTMLSession
from agentchat.settings import app_settings
import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent


async def crawl_today_ai_news(url=None):
    url = app_settings.mars["daily_url"] if not url else url

    # 创建HTML会话
    session = HTMLSession()

    try:
        # 发送请求获取页面
        response = session.get(url)

        # 执行JavaScript以加载动态内容
        response.html.render(sleep=2)  # 等待2秒让页面加载完成

        # 提取页面标题
        page_title = response.html.find('title', first=True).text if response.html.find('title',
                                                                                        first=True) else "未获取到标题"

        # 尝试多种方式提取内容
        # 1. 查找所有文章标题和摘要
        news_items = response.html.find('article')
        if not news_items:
            # 2. 尝试查找class包含"news"或"article"的div
            news_items = response.html.find('div[class*="news"], div[class*="article"]')
        if not news_items:
            # 3. 尝试查找所有带链接的标题和后续内容
            news_items = response.html.find('a[href*="/news/"]')

        news_links = []
        # 保存提取的内容
        news_content = []
        for item in news_items:
            # 获取文本内容
            text = item.text.strip()
            # 获取链接（如果有）
            link = item.absolute_links.pop() if item.absolute_links else ""

            if text:
                news_content.append(f"{text}\n链接: {link}\n")
                news_links.append(link)

        # 如果仍然没有找到内容，尝试提取所有可见文本
        if not news_content:
            logger.info("尝试提取所有可见文本...")
            all_paragraphs = response.html.find('p')
            for p in all_paragraphs:
                text = p.text.strip()
                if text and len(text) > 20:  # 过滤过短的文本
                    news_content.append(text)

        daily_news = f"页面标题: {page_title}\n\n"
        for content in news_content:
            daily_news += f"{content} \n {"-" * 50} \n"

        return daily_news, news_links
    except Exception as e:
        logger.error(f"爬取出错: {e}")
    finally:
        session.close()


async def crawl_single_ai_news(url):
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://news.aibase.com/"
    }

    try:
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        news_data = {}

        # 提取标题
        title_tag = soup.find("h1") or soup.find("title")
        news_data["title"] = title_tag.get_text(strip=True) if title_tag else "未找到标题"

        # 提取正文内容（包含所有可能的图片位置）
        # 使用更通用的方式获取正文区域
        content_tag = soup.find("article") or \
                      soup.find("div", class_=lambda x: x and ("content" in x or "article" in x)) or \
                      soup.find("main")

        if content_tag:
            content_parts = []
            # 遍历所有可能包含内容的元素（不只是直接子元素）
            for element in content_tag.find_all(['p', 'div', 'figure', 'img', 'section']):
                # 处理文本段落
                if element.name == 'p' and element.get_text(strip=True):
                    content_parts.append(element.get_text(strip=True))

                # 处理图片元素
                img_element = element if element.name == 'img' else element.find('img')
                if img_element:
                    img_url = img_element.get('src') or img_element.get('data-src')  # 考虑延迟加载的图片
                    if img_url:
                        # 补全相对路径
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = f"https://news.aibase.com{img_url}" if img_url.startswith(
                                '/') else f"https://news.aibase.com/{img_url}"
                        content_parts.append(f"[图片]：{img_url}")

            # 去重并保留顺序
            seen = set()
            unique_content = []
            for item in content_parts:
                if item not in seen:
                    seen.add(item)
                    unique_content.append(item)

            news_data["content"] = "\n\n".join(unique_content)
        else:
            #  fallback: 提取所有段落和图片
            all_elements = soup.find_all(['p', 'img'])
            content_parts = []
            for elem in all_elements:
                if elem.name == 'p' and elem.get_text(strip=True):
                    content_parts.append(elem.get_text(strip=True))
                elif elem.name == 'img':
                    img_url = elem.get('src') or elem.get('data-src')
                    if img_url:
                        content_parts.append(f"![图片]：{img_url}")
            news_data["content"] = "\n\n".join(content_parts) if content_parts else "未找到正文内容"

        return news_data["title"], news_data["content"]

    except Exception as e:
        logger.error(f"错误：{e}")
        return None, None

if __name__ == "__main__":
    target_url = "https://news.aibase.com/zh/news"
    print(f"开始爬取 {target_url} ...")
    crawl_today_ai_news(target_url)
    print("爬取完成")

