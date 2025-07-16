import os
import json

from loguru import logger
from sqlmodel import SQLModel

from agentchat.database import engine, SystemUser
from agentchat.api.services.agent import AgentService
from agentchat.api.services.llm import LLMService
from agentchat.api.services.tool import ToolService
from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.mcp_server import MCPService
from agentchat.database.models.user import AdminUser
from agentchat.services.mcp.manager import MCPManager
from agentchat.settings import app_settings


# 创建MySQL数据表
async def init_database():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Create MySQL Table Successful")
    except Exception as err:
        logger.error(f"Create MySQL Table Error: {err}")


# 初始化默认工具
async def init_default_agent():
    try:
        # if redis_client.setNx('init_default_agent', '1'):
        result = await AgentService.get_agent()
        if len(result) == 0:
            logger.info("Begin Init Agent In Mysql")

            await insert_tools_to_mysql()  # 初始化工具
            await insert_llm_to_mysql()  # 初始化LLM
            await insert_agent_to_mysql()  # 初始化Agent
        else:
            logger.info("Init Agent Already")
    except Exception as err:
        logger.error(f"Init Default Agent Error: {err}")


async def update_system_mcp_server():
    try:
        mcp_server = await MCPService.get_all_servers(SystemUser)
        # 如果数据库中无数据才会加载默认的MCP Server Json文件
        if len(mcp_server):
            await update_mcp_server_into_mysql(True)
        else:
            await update_mcp_server_into_mysql(False)
    except Exception as err:
        logger.error(f"Init System MCP Server Error: {err}")


async def insert_agent_to_mysql():
    llm = await LLMService.get_one_llm()

    tools = await ToolService.get_tools_data()
    for tool in tools:
        await AgentService.create_agent(name=tool["zh_name"] + '助手',
                                        description=tool["description"],
                                        user_id=SystemUser,
                                        llm_id=llm["llm_id"],
                                        tool_ids=[tool["tool_id"]],
                                        knowledge_ids=[],
                                        logo_url=app_settings.logo.get("agent_url"),
                                        is_custom=False,
                                        mcp_ids=[],
                                        system_prompt="")


# 认定OS下有一个默认LLM API KEY
async def insert_llm_to_mysql():
    api_key = app_settings.multi_models.qwen2.api_key
    base_url = app_settings.multi_models.qwen2.base_url
    model = app_settings.multi_models.qwen2.model_name
    llm_type = 'LLM'
    provider = 'Qwen'

    await LLMService.create_llm(user_id=SystemUser, model=model, llm_type=llm_type,
                                api_key=api_key, base_url=base_url, provider=provider)


# 初始化默认的Tool
async def insert_tools_to_mysql():
    tools = await load_default_tool()

    for tool in tools:
        zh_name = tool['zh_name']
        en_name = tool['en_name']
        logo_url = tool['logo_url']
        description = tool['description']

        await ToolService.create_tool(zh_name=zh_name, en_name=en_name, logo_url=logo_url,
                                      description=description, user_id=SystemUser)


# 更新MCP Server的信息到数据库中
async def update_mcp_server_into_mysql(has_mcp_server: bool):
    mcp_manager = MCPManager(timeout=10)

    # 判断是不是不是首次连接
    if has_mcp_server:
        # 超过七天才有更新MCP Server的策略
        if await MCPService.mcp_server_need_update():
            servers = await MCPService.get_all_servers(AdminUser)
            logger.info("MCP Server 最新版已更新到数据库！")
        else:
            return
    else:
        servers = await load_system_mcp_server()

    servers_info = []
    for server in servers:
        servers_info.append({"type": server["type"],
                             "url": server["url"],
                             "server_name": server["server_name"]})

    await mcp_manager.connect_mcp_servers(servers_info)
    servers_params = await mcp_manager.show_mcp_tools()

    # 通过MCP Server名称获取信息
    async def get_config_from_server_name(server_name):
        for server in servers:
            if server["server_name"] == server_name:
                return server
        return None

    # 解析Params中的工具列表
    async def get_tools_name_from_params(tools_params: dict):
        tools_name = []
        for tool in tools_params:
            tools_name.append(tool["name"])
        return tools_name

    for key, params in servers_params.items():
        server = await get_config_from_server_name(key)
        tools_name = await get_tools_name_from_params(params)
        if has_mcp_server:
            await MCPService.update_mcp_server(mcp_server_id=server["mcp_server_id"],
                                               tools=tools_name, params=params)
        else:
            await MCPService.create_mcp_server(key, SystemUser, "Admin", server["url"], server["type"],
                                               server["config"], tools_name, params, server["config_enabled"], server["logo_url"])


async def load_default_tool():
    with open('./agentchat/data/tool.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    return result


async def load_system_mcp_server():
    with open('./agentchat/data/mcp_server.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    return result

# --------------------------------------
# 下面是0.1版本，不做修改
# --------------------------------------

# Agent的json文件加载
# def load_agent_openai():
#     with open("TOOL_OPENAI", 'r', encoding='utf-8') as f:
#         result = json.load(f)
#
#     return result
#
#
# # 将工具的信息插入到MySQL
# def agent_insert_mysql(type: str = "openai"):
#     result = load_agent_openai()
#
#     for data in result:
#         name = data.get('name')
#         description = data.get('description')
#         logo = data.get('logo')
#         parameter = data
#
#         AgentService.create_agent(name=name,
#                                   description=description,
#                                   logo=logo,
#                                   parameter=json.dumps(parameter, ensure_ascii=False),
#                                   type=type,
#                                   is_custom=False)
