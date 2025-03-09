import os
import asyncio

from schema.chunk import ChunkModel
from services.rag.doc_split.text import text_parser
from services.rag.doc_split.markdown import markdown_parser
from core.models import async_client


class DocParser:

    @classmethod
    async def parse_doc_into_chunks(cls, file_id, file_path, knowledge_id, max_concurrent_tasks=5):
        file_suffix = file_path.split('.')[-1]
        chunks = []
        if file_suffix == 'md':
            chunks = await markdown_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix == 'txt':
            chunks = await text_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        """其他文档"""

        # 创建信号量，限制最大并发任务数
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        tasks = [asyncio.create_task(cls.generate_summary(chunk, semaphore)) for chunk in chunks]
        chunks = asyncio.gather(*tasks)

        return chunks

    @classmethod
    async def generate_summary(cls, chunk: ChunkModel, semaphore):
        async with semaphore:
            prompt = f"""
                你是一个专业的摘要生成助手，请根据以下要求为文本生成一段摘要：
                ## 需要总结的文本：
                {chunk.content}
                ## 要求：
                1. 摘要字数控制在 100 字左右。
                2. 摘要中仅包含文字和字母，不得出现链接或其他特殊符号。
                3. 只输出摘要部分，不准输出 `以下是文本的摘要` 等字段
            """
            response = async_client.ainvoke(prompt)
            chunk.summary = response

            return chunk

doc_parser = DocParser()