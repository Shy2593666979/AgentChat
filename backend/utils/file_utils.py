# encoding=utf-8
import json
import os.path
import tempfile
import logging
import aiofiles
from uuid import uuid4

def load_file_to_obj(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading scene prompts: {e}")
        return {}

async def save_upload_file(upload_file):
    # 创建临时文件夹
    temp = tempfile.mkdtemp()
    file_name = os.path.basename(upload_file.file_name)
    file_path = os.path.join(temp, file_name)
    async with aiofiles.open(file_path, 'wb') as file:
        content = await upload_file.read()
        await file.write(content)
    return file_path

async def get_oss_object_name(file_path, knowledge_id):
    file_name = os.path.basename(file_path)
    file_suffix = file_name.split('.')[-1]

    object_name = f"/{knowledge_id}/{os.path.splitext(file_name)}_{uuid4().hex}_{file_suffix}"
    return object_name

async def read_upload_file(file_path):
    async with aiofiles.open(file_path, 'r') as file:
        content = await file.read()
    return content