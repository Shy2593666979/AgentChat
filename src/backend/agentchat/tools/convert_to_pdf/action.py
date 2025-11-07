import os
import tempfile
import subprocess

from langchain.tools import tool
from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.utils.file_utils import get_object_name_from_aliyun_url, get_save_tempfile
from agentchat.utils.helpers import get_now_beijing_time


@tool("docx_to_pdf", parse_docstring=True)
def convert_to_pdf(file_url: str):
    """
    将用户上传的 DOCX 文件转换为 PDF 文件并返回链接。

    Args:
        file_url (str): 用户上传的 DOCX 文件链接。

    Returns:
        str: 转换后的 PDF 文件链接。
    """
    return _convert_to_pdf(file_url)

def _convert_to_pdf(file_url):
    """将用户上传的文件解析成PDF"""
    object_name = get_object_name_from_aliyun_url(file_url)
    file_name = file_url.split("/")[-1]
    file_path = get_save_tempfile(file_name)
    aliyun_oss.download_file(object_name, file_path)

    if not os.path.isfile(file_path):
        return f"上传的文件: {os.path.basename(file_path)}没有被接收到,重新上传试试呢~~~"

    # 获取文件扩展名
    file_extension = file_path.split('.')[-1].lower()

    # 检查LibreOffice支持的格式
    supported_formats = ['docx', 'doc', 'odt', 'rtf', 'txt', 'html', 'htm', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'odp']
    if file_extension not in supported_formats:
        return f"目前支持的格式有: {', '.join(supported_formats)},暂不支持您上传的{file_extension}格式文件,再等段时间吧~~~"

    try:
        # 创建临时输出目录
        output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)

        # 获取不带扩展名的文件名
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        pdf_filename = f"{base_filename}.pdf"
        local_pdf_path = os.path.join(output_dir, pdf_filename)

        # 使用LibreOffice转换为PDF
        # 注意：需要在系统上安装LibreOffice
        libreoffice_cmd = [
            'libreoffice', '--headless', '--convert-to', 'pdf',
            '--outdir', output_dir, file_path
        ]
        
        process = subprocess.run(
            libreoffice_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 检查转换是否成功
        if process.returncode != 0:
            return f'您的{os.path.basename(file_path)}文件解析失败: {process.stderr},换个文件再来试试呢~~~'

        # 确认生成的PDF文件路径
        local_pdf_path = os.path.join(output_dir, pdf_filename)
        if not os.path.exists(local_pdf_path):
            return f'您的{os.path.basename(file_path)}文件解析失败,换个文件再来试试呢~~~'

        # 上传到OSS
        oss_object_name = f"convert_pdf/{pdf_filename}"
        aliyun_oss.upload_local_file(oss_object_name, local_pdf_path)

        # 生成下载URL
        url = aliyun_oss.sign_url_for_get(oss_object_name)
        now_time = get_now_beijing_time(delta=1)

        # 清理临时文件
        try:
            os.remove(file_path)
            os.remove(local_pdf_path)
            os.rmdir(output_dir)
        except OSError:
            pass  # 忽略清理错误

        return f'您的{os.path.basename(file_path)}文件解析成功,下载路径为:{url},请在{now_time} 前进行下载,超过时间就会失效~~~'

    except Exception as e:
        return f'您的{os.path.basename(file_path)}文件解析失败: {str(e)},换个文件再来试试呢~~~'