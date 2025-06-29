import os
import tempfile

import aiofiles
import pymupdf4llm
import pathlib
from urllib.parse import urljoin
from loguru import logger

from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.services.rag.doc_parser.markdown import markdown_parser
from agentchat.settings import app_settings
from agentchat.utils.file_utils import get_aliyun_oss_base_path, get_images_dir, generate_unique_filename

class PDFParser:

    def __init__(self):
        pass

    async def convert_markdown(self, file_path: str):
        images_dir = get_images_dir()
        markdown_dir = get_images_dir()
        md_text_words = pymupdf4llm.to_markdown(
            doc=file_path,
            write_images=True,
            image_path=images_dir,
            image_format="png",
            dpi=300
        )
        markdown_output = os.path.join(markdown_dir, generate_unique_filename(file_path, "md"))
        output_markdown_file = pathlib.Path(markdown_output)
        output_markdown_file.write_bytes(md_text_words.encode())
        logger.info(f"PDF Convert MarkDown Successful！MarkDown Path: {output_markdown_file}")

        async with aiofiles.open(output_markdown_file, "r") as file:
            file_content = file.read()
            oss_base_path = get_aliyun_oss_base_path(os.path.basename(file_path))
            sign_url = urljoin(app_settings.aliyun_oss["base_url"], oss_base_path)

            aliyun_oss.sign_url_for_get(sign_url)
            aliyun_oss.upload_file(sign_url, file_content)

        return output_markdown_file

    async def parse_into_chunks(self, file_id, file_path, knowledge_id):
        markdown_file = await self.convert_markdown(file_path)
        return await markdown_parser.parse_into_chunks(file_id, markdown_file, knowledge_id)

pdf_parser = PDFParser()