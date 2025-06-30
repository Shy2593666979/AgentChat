# encoding=utf-8
import json
import os.path
import tempfile
import logging
import aiofiles
from uuid import uuid4

from agentchat.settings import app_settings
from agentchat.utils.date_utils import get_beijing_date_str

def load_file_to_obj(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading scene prompts: {e}")
        return {}

def get_aliyun_oss_base_path(file_name):
    beijing_time = get_beijing_date_str()
    file_type = get_file_type(file_name)

    # 改成文件唯一文件名称
    new_file_name = reset_file_name(file_name)

    # 2024-10-26/png/a12xk25jn34kn5.png
    return f"{beijing_time}/{file_type}/{new_file_name}"

def get_file_type(file_name):
    return file_name.split(".")[-1]

def reset_file_name(file_name):
    file_type = get_file_type(file_name)

    return f"{uuid4().hex}.{file_type}"

async def save_upload_file(upload_file):
    # 创建临时文件夹
    temp = tempfile.mkdtemp()
    file_name = os.path.basename(upload_file.file_name)
    file_path = os.path.join(temp, file_name)
    async with aiofiles.open(file_path, 'wb') as file:
        content = await upload_file.read()
        await file.write(content)
    return file_path

def get_save_tempfile(file_name):
    # 创建临时文件夹
    temp = tempfile.mkdtemp()
    file_name = os.path.basename(file_name)
    file_path = os.path.join(temp, file_name)
    return file_path

def get_images_dir(images_dir: str="images"):
    # 创建临时文件夹
    temp = tempfile.mkdtemp()
    file_path = os.path.join(temp, images_dir)
    return file_path

def get_markdown_dir():
    return get_images_dir("markdown")

# 只对PDF ---> Markdown使用
def get_convert_markdown_images_dir():
    # 创建临时文件夹
    temp = tempfile.mkdtemp()
    images_path = os.path.join(temp, "images")
    return temp, images_path

def generate_unique_filename(file_name: str, file_suffix: str=None) -> str:
    file_name = os.path.basename(file_name)
    if file_suffix:
        return f"{file_name.split(".")[0]}_{uuid4().hex}.{file_suffix}"
    else:
        return f"{file_name.split(".")[0]}_{uuid4().hex}.{file_name.split(".")[-1]}"

async def get_oss_object_name(file_path, knowledge_id):
    file_name = os.path.basename(file_path)
    file_suffix = file_name.split('.')[-1]

    object_name = f"/{knowledge_id}/{os.path.splitext(file_name)}_{uuid4().hex}_{file_suffix}"
    return object_name

async def read_upload_file(file_path):
    async with aiofiles.open(file_path, 'r') as file:
        content = await file.read()
    return content