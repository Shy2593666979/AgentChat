import os
import tempfile
from pdf2docx import Converter
from langchain.tools import tool

from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.utils.file_utils import get_object_name_from_aliyun_url, get_save_tempfile
from agentchat.utils.helpers import get_now_beijing_time


@tool(parse_docstring=True)
def convert_to_docx(file_url: str):
    """
    将用户上传的 PDF 文件链接转换为 DOCX 文件链接。

    Args:
        file_url (str): 用户上传的 PDF 文件链接。

    Returns:
        str: 转换后的 DOCX 文件链接。
    """
    return _convert_to_docx(file_url)

def _convert_to_docx(file_url: str):
    """将用户上传的文件解析成Docx"""
    object_name = get_object_name_from_aliyun_url(file_url)
    file_name = file_url.split("/")[-1]
    file_path = get_save_tempfile(file_name)
    aliyun_oss.download_file(object_name, file_path)


    if not os.path.isfile(file_path):
        return f"上传的文件: {os.path.basename(file_path)}没有被接收到，重新上传试试呢~~~"
    if file_path.split('.')[-1] != 'pdf':
        return f"目前只支持PDF文件呢，暂不支持您上传{file_path.split('.')[-1]}格式的文件，再等段时间吧~~~"

    # 创建临时文件夹
    output_dir = tempfile.mkdtemp()
    os.makedirs(output_dir, exist_ok=True)

    local_file_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}.docx")

    try:
        cv = Converter(file_path)
        cv.convert(
            local_file_path,
            start=0,
            end=None,
            layout_kwargs={  # 调整布局参数
                "detect_vertical_text": True,  # 识别垂直文本
                "char_margin": 1.0,            # 字符间距容差
                "line_overlap": 0.5,           # 行重叠阈值
            }
        )
        cv.close()
    except Exception as err:
        return f'您的{os.path.basename(file_path)}文件解析失败，换个文件再来试试呢~~~'

    oss_object_name = f"convert_docx/{os.path.splitext(file_name)[0]}.docx"

    aliyun_oss.upload_local_file(oss_object_name, local_file_path)

    url = aliyun_oss.sign_url_for_get(oss_object_name)
    now_time = get_now_beijing_time(delta=1)

    return f'您的{os.path.basename(file_path)}文件转换成功，[点击下载文件]({url})，请在{now_time} 前进行下载，超过时间就会失效~~~'