import os
import tempfile
from typing import Type

import pypandoc
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.utils.file_utils import get_object_name_from_aliyun_url, get_save_tempfile
from agentchat.utils.helpers import get_now_beijing_time


class ConvertPdfInput(BaseModel):
    file_url: str = Field(description='用户上传的文件URL路径')


class ConvertPdfTool(BaseTool):
    name: str = 'convert_to_pdf'
    description: str = '将用户上传的文件解析成PDF'
    args_schema: Type[BaseModel] = ConvertPdfInput

    def _run(self, file_url):
        return convert_to_pdf(file_url)


class ConvertToPdfError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)


def convert_to_pdf(file_url):
    """将用户上传的文件解析成PDF"""
    object_name = get_object_name_from_aliyun_url(file_url)
    file_name = file_url.split("/")[-1]  # Fixed typo: spilt -> split
    file_path = get_save_tempfile(file_name)
    aliyun_oss.download_file(object_name, file_path)

    if not os.path.isfile(file_path):
        return f"上传的文件: {os.path.basename(file_path)}没有被接收到，重新上传试试呢~~~"

    # Get file extension
    file_extension = file_path.split('.')[-1].lower()

    # Check supported formats for pypandoc
    supported_formats = ['docx', 'doc', 'md', 'markdown', 'txt', 'html', 'htm', 'rtf', 'odt']
    if file_extension not in supported_formats:
        return f"目前支持的格式有: {', '.join(supported_formats)}，暂不支持您上传的{file_extension}格式文件，再等段时间吧~~~"

    try:
        # Create temporary output file
        output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)

        # Get base filename without extension
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        pdf_filename = f"{base_filename}.pdf"
        local_pdf_path = os.path.join(output_dir, pdf_filename)

        # Convert to PDF using pypandoc
        pypandoc.convert_file(
            source_file=file_path,
            to='pdf',
            outputfile=local_pdf_path,
            extra_args=['--pdf-engine="D:\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"']  # or use 'wkhtmltopdf' if available
        )

        # Check if conversion was successful
        if not os.path.exists(local_pdf_path):
            return f'您的{os.path.basename(file_path)}文件解析失败，换个文件再来试试呢~~~'

        # Upload to OSS
        oss_object_name = f"convert_pdf/{pdf_filename}"
        aliyun_oss.upload_local_file(oss_object_name, local_pdf_path)

        # Generate download URL
        url = aliyun_oss.sign_url_for_get(oss_object_name)
        now_time = get_now_beijing_time(delta=1)

        # Clean up temporary files
        try:
            os.remove(file_path)
            os.remove(local_pdf_path)
            os.rmdir(output_dir)
        except OSError:
            pass  # Ignore cleanup errors

        return f'您的{os.path.basename(file_path)}文件解析成功，下载路径为：{url}，请在{now_time} 前进行下载，超过时间就会失效~~~'

    except Exception as e:
        return f'您的{os.path.basename(file_path)}文件解析失败: {str(e)}，换个文件再来试试呢~~~'