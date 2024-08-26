import json

from sqlmodel import SQLModel, create_engine
from database.model import HistoryTable, DialogTable
from database.base import Agent
from loguru import logger
from config.service_config import MYSQL_URL, TOOL_OPENAI, LOGO_PREFIX
from cache.redis import redis_client
from database.base import Agent


# 创建MySQL数据表
def init_database():
    try:
        engine = create_engine(MYSQL_URL)
        SQLModel.metadata.create_all(engine)
        logger.info("mysql table is successful")
    except Exception as err:
        logger.error(f"create mysql table appear error: {err}")

# 初始化默认工具
def init_default_agent():
    try:
        if redis_client.setNx('init_default_agent', '1'):
            result = Agent.get_agent()
            if len(result) == 0:
                logger.info("begin init agent in mysql")
                agent_insert_mysql()
            else:
                logger.info("init agent already")
    except Exception as err:
        logger.error(f"init default agent appear error: {err}")

# 将工具的信息插入到MySQL
def agent_insert_mysql(type: str="openai"):
    result = load_agent_openai()

    for data in result:
        name = data.get('name')
        description = data.get('description')
        logo = LOGO_PREFIX + data.get('logo')
        parameter = data

        Agent.create_agent(name=name,
                           description=description,
                           logo=logo,
                           parameter=json.dumps(parameter, ensure_ascii=False),
                           type=type,
                           isCustom=False)


# 去Agent的json文件加载
def load_agent_openai():
    with open(TOOL_OPENAI, 'r', encoding='utf-8') as f:
        result = json.load(f)

    return result
