from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_and_parse(url):
    # 使用 Playwright 抓取 HTML
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        html_content = page.content()
        browser.close()

    print(html_content)
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, "lxml")

    # 提取所有 <a> 标签中的 href 属性和文本
    links = []
    for a_tag in soup.find_all("a", href=True):  # 查找所有带有 href 属性的 <a> 标签
        link_text = a_tag.get_text(strip=True)  # 获取链接的文本内容
        link_url = a_tag["href"]  # 获取链接的 URL
        links.append({"text": link_text, "url": link_url})

    return links

if __name__ == "__main__":
    url = "https://talent.ele.me/campus/position-list?campusType=freshman&lang=zh"  # 替换为你想抓取的网址
    parsed_links = scrape_and_parse(url)

    # 打印提取到的链接
    for link in parsed_links:
        print(f"文本: {link['text']}, 链接: {link['url']}")