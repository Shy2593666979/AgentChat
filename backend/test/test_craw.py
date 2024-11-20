import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://baijiahao.baidu.com/s?id=1816250438544027909&wfr=spider&for=pc")
        print(result.markdown)

        with open("output.md", "w", encoding="utf-8") as file:
            file.write(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())