import os
import asyncio

from agentchat.services.rag.doc_parser.excel import excel_to_txt
from agentchat.services.rag.doc_parser.image import image_to_txt
from agentchat.services.rag.doc_parser.other_file import other_file_to_txt
from agentchat.services.rag.doc_parser.pptx import pptx_parser
from agentchat.core.models.manager import ModelManager
from agentchat.services.rag.doc_parser.docx import docx_parser
from agentchat.services.rag.doc_parser.pdf import pdf_parser
from agentchat.services.rag.doc_parser.text import text_parser
from agentchat.services.rag.doc_parser.markdown import markdown_parser
from agentchat.schema.chunk import ChunkModel
from agentchat.settings import app_settings

IMAGE_SUFFIXES = {"jpg", "jpeg", "png", "bmp", "webp", "tiff"}
TEXT_LIKE_SUFFIXES = {"txt", "json", "html", "htm", "csv"}
EXCEL_SUFFIXES = {"xls", "xlsx"}

class DocParser:

    @classmethod
    async def parse_doc_into_chunks(cls, file_id, file_path, knowledge_id, max_concurrent_tasks=5):
        file_suffix = file_path.split('.')[-1]
        chunks = []
        if file_suffix == 'md':
            chunks = await markdown_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix == 'txt':
            chunks = await text_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix == 'docx':
            chunks = await docx_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix == 'pdf':
            chunks = await pdf_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix == 'pptx':
            chunks = await pptx_parser.parse_into_chunks(file_id, file_path, knowledge_id)
        elif file_suffix in IMAGE_SUFFIXES: # 图片类型
            new_file_path = image_to_txt(file_path)
            chunks = await text_parser.parse_into_chunks(file_id, new_file_path, knowledge_id)
        elif file_suffix in EXCEL_SUFFIXES: # 表格类型
            new_file_path = excel_to_txt(file_path)
            chunks = await text_parser.parse_into_chunks(file_id, new_file_path, knowledge_id)
        elif file_suffix in TEXT_LIKE_SUFFIXES: # 可转化成Txt文件类型
            new_file_path = other_file_to_txt(file_path)
            chunks = await text_parser.parse_into_chunks(file_id, new_file_path, knowledge_id)
        """其他文档"""

        # 当开启chunk总结时才有该步骤
        if app_settings.rag.enable_summary:
            # 创建信号量，限制最大并发任务数
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            tasks = [asyncio.create_task(cls.generate_summary(chunk, semaphore)) for chunk in chunks]
            chunks = await asyncio.gather(*tasks)

        return chunks

    @classmethod
    async def generate_summary(cls, chunk: ChunkModel, semaphore):
        async_client = ModelManager.get_conversation_model()

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
            response = await async_client.ainvoke(prompt)
            chunk.summary = response.content

            return chunk

doc_parser = DocParser()