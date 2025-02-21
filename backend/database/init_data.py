import os
import json

from sqlmodel import SQLModel

from database import engine, SystemUser
from api.services.agent import AgentService
from loguru import logger
from api.services.llm import LLMService
from api.services.tool import ToolService
from settings import app_settings


# 创建MySQL数据表
def init_database():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("mysql table is successful")
    except Exception as err:
        logger.error(f"create mysql table appear error: {err}")


# 初始化默认工具
def init_default_agent():
    try:
        # if redis_client.setNx('init_default_agent', '1'):
        result = AgentService.get_agent()
        if len(result) == 0:
            logger.info("begin init agent in mysql")

            insert_tools_to_mysql() # 初始化工具
            insert_llm_to_mysql()   # 初始化LLM
            insert_agent_to_mysql() # 初始化Agent
        else:
            logger.info("init agent already")
    except Exception as err:
        logger.error(f"init default agent appear error: {err}")

def insert_agent_to_mysql():
    llm = LLMService.get_one_llm()

    tools = ToolService.get_tools_data()
    for tool in tools:
        AgentService.create_agent(name=tool.zh_name + '助手',
                                  description=tool.description,
                                  user_id=SystemUser,
                                  llm_id=llm.llm_id,
                                  tool_id=[tool.tool_id],
                                  logo=app_settings.logo.get('agent'),
                                  is_custom=False)


# 认定OS下有一个默认LLM API KEY
def insert_llm_to_mysql():
    api_key = os.getenv('API_KEY')
    base_url = os.getenv('BASE_URL')
    model = os.getenv('MODEL') or 'GPT-4'
    llm_type = os.getenv('TYPE') or 'LLM'
    provider = os.getenv('PROVIDER') or 'OpenAI'


    if model and api_key and base_url and provider:
        LLMService.create_llm(user_id=SystemUser, model=model, llm_type=llm_type,
                              api_key=api_key, base_url=base_url, provider=provider)

# 初始化默认的Tool
def insert_tools_to_mysql():
    tools = load_default_tool()

    for tool in tools:
        zh_name = tool['zh_name']
        en_name = tool['en_name']
        description = tool['description']

        ToolService.create_tool(zh_name=zh_name, en_name=en_name,
                                description=description, user_id=SystemUser)

def load_default_tool():
    with open('./data/tool.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    return result

# --------------------------------------
# 下面是0.1版本，不做修改
# --------------------------------------

# Agent的json文件加载
def load_agent_openai():
    with open("TOOL_OPENAI", 'r', encoding='utf-8') as f:
        result = json.load(f)

    return result

# 将工具的信息插入到MySQL
def agent_insert_mysql(type: str = "openai"):
    result = load_agent_openai()

    for data in result:
        name = data.get('name')
        description = data.get('description')
        logo = data.get('logo')
        parameter = data

        AgentService.create_agent(name=name,
                                  description=description,
                                  logo=logo,
                                  parameter=json.dumps(parameter, ensure_ascii=False),
                                  type=type,
                                  is_custom=False)
