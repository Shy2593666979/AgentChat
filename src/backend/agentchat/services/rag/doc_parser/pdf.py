import asyncio
import os
import tempfile
import aiofiles
import pymupdf4llm
import pathlib
from urllib.parse import urljoin
from loguru import logger

from agentchat.settings import app_settings
from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.services.rag.doc_parser.markdown import markdown_parser
from agentchat.services.rewrite.markdown_rewrite import markdown_rewriter
from agentchat.utils.file_utils import get_aliyun_oss_base_path, get_convert_markdown_images_dir, \
    generate_unique_filename


class PDFParser:

    def __init__(self):
        pass

    async def convert_markdown(self, file_path: str):
        # 保证markdown和images 在同一目录下
        markdown_dir, images_dir = get_convert_markdown_images_dir()
        md_text_words = pymupdf4llm.to_markdown(
            doc=file_path,
            write_images=True,
            image_path=images_dir,
            image_format="png",
            dpi=300
        )
        markdown_output_path = os.path.join(markdown_dir, generate_unique_filename(file_path, "md"))
        output_markdown_file = pathlib.Path(markdown_output_path)
        output_markdown_file.write_bytes(md_text_words.encode())
        logger.info(f"PDF Convert MarkDown Successful！MarkDown Path: {output_markdown_file}")

        # 上传Markdown中的图片到OSS
        file_upload_url_map = await self.upload_folder_to_oss(images_dir)
        # 对Markdown中的图片进行重写
        await markdown_rewriter.run_rewrite(markdown_output_path, file_upload_url_map)
        # 重写后的Markdown上传到OSS中
        await self.upload_file_to_oss(markdown_output_path)

        return markdown_output_path

    async def parse_into_chunks(self, file_id, file_path, knowledge_id):
        markdown_file = await self.convert_markdown(file_path)
        return await markdown_parser.parse_into_chunks(file_id, markdown_file, knowledge_id)

    async def upload_file_to_oss(self, file_path):
        async with aiofiles.open(file_path, "rb") as file:
            file_content = await file.read()
            oss_object_name = get_aliyun_oss_base_path(os.path.basename(file_path))
            sign_url = urljoin(app_settings.aliyun_oss["base_url"], oss_object_name)

            aliyun_oss.sign_url_for_get(sign_url)
            aliyun_oss.upload_file(oss_object_name, file_content)
            return sign_url

    async def upload_folder_to_oss(self, file_dir):
        tasks = []
        for file_name in os.listdir(file_dir):
            file_path = os.path.join(file_dir, file_name)
            tasks.append(self.upload_file_to_oss(file_path))
        # file_name(Key): oss_url(Value)
        file_upload_url_map: dict = {}
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for file_name, result in zip(os.listdir(file_dir), results):
            if isinstance(result, Exception):
                logger.error(f"上传文件 {file_name} 失败，错误信息：{result}")
            else:
                file_upload_url_map[file_name] = result
                logger.info(f"文件 {file_name} 上传成功")

        return file_upload_url_map


pdf_parser = PDFParser()
