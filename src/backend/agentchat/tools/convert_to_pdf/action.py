import os
import subprocess
from typing import Type

import tempfile
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
        return convert_file_to_pdf(file_url)

class ConvertToPdfError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)


def convert_file_to_pdf(file_url):
    """将用户上传的文件解析成PDF"""
    object_name = get_object_name_from_aliyun_url(file_url)
    file_name = file_url.spilt("/")[-1]
    file_path = get_save_tempfile(file_name)
    aliyun_oss.download_file(object_name, file_path)

    if not os.path.isfile(file_path):
        return f"上传的文件: {os.path.basename(file_path)}没有被接收到，重新上传试试呢~~~"
    if file_path.split('.')[-1] != 'docx':
        return f"目前只支持Docx文件呢，暂不支持您上传{file_path.split('.')[-1]}格式的文件，再等段时间吧~~~"

    # 创建临时文件夹
    output_dir = tempfile.mkdtemp()
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        'soffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', str(output_dir),
        str(file_path)
    ]

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode != 0:
        return f'您的{os.path.basename(file_path)}文件解析失败，换个文件再来试试呢~~~'

    oss_object_name = f"/convert_pdf/{os.path.splitext(file_path)}.pdf"
    local_file_path = os.path.join(output_dir, f"{os.path.splitext(file_path)}.pdf")
    aliyun_oss.upload_local_file(oss_object_name, local_file_path)

    url = aliyun_oss.sign_url_for_get(oss_object_name)
    now_time = get_now_beijing_time(delta=1)

    return f'您的{os.path.basename(file_path)}文件解析成功，下载路径为：{url}，请在{now_time} 前进行下载，超过时间就会失效~~~'