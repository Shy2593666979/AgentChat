import json

from sqlmodel import SQLModel, create_engine
from database.model import HistoryTable, DialogTable
from database.base import Tool
from loguru import logger
from config.service_config import MYSQL_URL, TOOL_OPENAI
from cache.redis import redis_client
from database.base import Tool


# 创建MySQL数据表
def init_database():
    try:
        engine = create_engine(MYSQL_URL)
        SQLModel.metadata.create_all(engine)
        logger.info("create mysql table is successful")
    except Exception as err:
        logger.error(f"create mysql table appear error: {err}")

# 初始化默认工具
def init_default_tool():
    try:
        if redis_client.setNx('init_default_tool', '1'):
            result = Tool.get_tool()
            if len(result) == 0:
                logger.info("begin init tool in mysql")
                tool_insert_mysql()
            else:
                logger.info("init tool already")
    except Exception as err:
        logger.error(f"init default tool appear error: {err}")

# 将工具的信息插入到MySQL
def tool_insert_mysql(type: str="openai"):
    result = load_tool_openai()

    for data in result:
        name = data.get('name')
        description = data.get('description')
        parameter = data
        Tool.create_tool(name=name, description=description, parameter=json.dumps(parameter), type=type)


# 去Tool的json文件加载
def load_tool_openai():
    with open(TOOL_OPENAI, 'r', encoding='utf-8') as f:
        result = json.load(f)

    return result
