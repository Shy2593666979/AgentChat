import asyncio
import json
import time
import random
from typing import List, Optional, Union
from loguru import logger
from langchain.tools import tool
from langgraph.config import get_stream_writer

from functools import wraps
from agentchat.api.services.llm import LLMService
from agentchat.api.services.tool import ToolService
from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.agent import AgentService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.mars import Mars_Autobuild_Answer_Prompt
from agentchat.settings import app_settings

def return_chunk_format(type: str, data: Union[str, dict]):
    return {
        "type": type,
        "time": time.time(),
        "data": data
    }


def dynamic_docstring(template_func):
    """装饰器，用于动态生成文档字符串"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 在函数调用时动态生成文档字符串
            if hasattr(template_func, '__call__'):
                # 如果template_func是异步函数
                if asyncio.iscoroutinefunction(template_func):
                    user_id = kwargs.get('user_id') or (args[0] if args else None)
                    auto_build_prompt = await template_func(user_id)
                else:
                    auto_build_prompt = template_func()

                # 替换占位符
                original_doc = func.__doc__ or ""
                func.__doc__ = original_doc.replace("{{{user_configs_placeholder}}}", auto_build_prompt)

            return await func(*args, **kwargs)

        return wrapper

    return decorator

async def construct_auto_build_prompt(user_id: Optional[str]) -> str:
    """
    异步构建自动创建智能体的提示信息，包含可用的模型、工具等信息

    Args:
        user_id: 用户ID，用于获取该用户可见的资源

    Returns:
        包含各类可用资源信息的提示字符串
    """
    # 并行获取各类资源信息，提高效率
    llms_task = LLMService.get_visible_llm(user_id)
    tools_task = ToolService.get_visible_tool_by_user(user_id)
    mcp_servers_task = MCPService.get_all_servers(user_id)
    knowledges_task = KnowledgeService.select_knowledge(user_id)

    # 等待所有任务完成
    llms_result, tools_result, mcp_servers_result, knowledges_result = await asyncio.gather(
        llms_task, tools_task, mcp_servers_task, knowledges_task
    )

    # 格式化各类资源信息
    llms_info = "\n".join([f"{idx+1}. 模型名称: {llm["model"]}, 提供商: {llm["provider"]}"
                           for idx, llm in enumerate(llms_result.get("LLM", []))])

    tools_info = "\n".join([f"{idx+1}. 插件工具名称: {tool['en_name']}, 工具描述: {tool['description']}"
                            for idx, tool in enumerate(tools_result)])

    mcp_servers_info = "\n".join([f"{idx+1}. MCP 服务名称: {mcp_server['server_name']}"
                                  for idx, mcp_server in enumerate(mcp_servers_result)])

    knowledges_info = "\n".join([f"{idx+1}. 知识库名称: {knowledge['name']}, 描述: {knowledge['description']}"
                                 for idx, knowledge in enumerate(knowledges_result)])

    return f"""
        - 模型（llm_name）：
        {llms_info or '无可用模型'}
        ---------------------------------------------
    
        - 插件工具（tools_name）：
        {tools_info or '无可用插件工具'}
        ---------------------------------------------
    
        - MCP 服务（mcp_servers_name）：
        {mcp_servers_info or '无可用MCP服务'}
        ---------------------------------------------
    
        - 知识库（knowledges_name）：
        {knowledges_info or '无可用知识库'}
        ---------------------------------------------
        请根据用户提供的描述以及可选的智能体配置，提取相关信息并匹配到上述参数中。
    """

@tool(parse_docstring=True)
async def auto_build_agent(
        agent_name: str,
        agent_description: str,
        llm_name: str,
        tools_name: List[str] = [],
        knowledges_name: List[str] = [],
        mcp_servers_name: List[str] = [],
        user_id: Optional[str]=None
):
    """
    自动构建智能体工具, 通过提取用户的输入信息来精准的帮助用户来快速创建一个智能体, 智能体配置必须选择的是可选择配置中的; 可选择智能体配置:{{{user_configs_placeholder}}}
    
    Args:
        agent_name: str, 用户想要构建智能体的名称
        agent_description: str, 对智能体功能、用途及特性的详细描述，帮助系统理解智能体的定位和作用范围
        llm_name: str, 指定智能体所使用的大语言模型名称，需与系统支持的模型列表匹配，决定智能体的基础能力
        tools_name: List[str], 智能体可调用的工具名称列表，用于扩展智能体的功能边界
        knowledges_name: List[str], 智能体可访问的知识库名称列表，为智能体提供专业领域信息支持
        mcp_servers_name: List[str], 智能体可连接的MCP服务名称列表，用于实现与外部系统的数据交互和功能调用
        user_id: 当前用户ID，默认为None

    Returns:
        返回创建智能体成功或者失败的信息
    """
    # # 替换文档字符串中的占位符（用于schema生成）
    # auto_build_prompt = await construct_auto_build_prompt(user_id)
    # func = auto_build_agent
    # original_doc = func.__doc__
    # func.__doc__ = original_doc.replace("{{{user_configs_placeholder}}}", auto_build_prompt)
    writer = get_stream_writer()

    agent_message = ""
    try:
        if len(agent_name) < 2 or len(agent_name) > 10:
            error_message = f"智能体名称: {agent_name}, 不满足智能体名称要求的字符数限制, 字数要求大于等于2, 小于等于10"
            agent_message = error_message
            raise ValueError(error_message)

        if len(agent_description) > 200:
            error_message = f"智能体描述: {agent_description}, 不满足智能体描述要求的字符数限制, 字数要求小于200"
            agent_message = error_message
            raise ValueError(error_message)

        llm_id = await LLMService.get_llm_id_from_name(llm_name, user_id)

        tool_ids = await ToolService.get_tool_ids_from_name(tools_name if isinstance(tools_name, List) else [tools_name] , user_id)

        knowledge_ids = await KnowledgeService.get_knowledge_ids_from_name(knowledges_name if isinstance(knowledges_name, List) else [knowledges_name], user_id)

        mcp_server_ids = await MCPService.get_mcp_server_ids_from_name(mcp_servers_name if isinstance(mcp_servers_name, List) else [mcp_servers_name], user_id)

        await AgentService.create_agent(
            name=agent_name,
            description=agent_description,
            llm_id=llm_id,
            tool_ids=tool_ids,
            mcp_ids=mcp_server_ids,
            knowledge_ids=knowledge_ids,
            user_id=user_id,
            system_prompt="",
            logo_url=app_settings.default_config.get("agent_logo_url")
        )
        agent_message = f"您的智能体{agent_name}已经创建完毕, 请点击智能体页面进行查看 \n 如果想要创建更多的智能体, 请跟我说哦~"
    except Exception as err:
        agent_message = f"创建智能体失败,请根据该原因进行修改, 失败原因:{err}"
        logger.error(agent_message)
    finally:
        conversation_model = ModelManager.get_conversation_model()
        agent_content = Mars_Autobuild_Answer_Prompt.format(agent_info=f"模型：{llm_name}\n 工具: {tools_name}\n MCP 服务: {mcp_servers_name}\n 知识库: {knowledges_name}", agent_message=agent_message)
        async for chunk in conversation_model.astream(agent_content):
            writer(
                return_chunk_format("response_chunk", chunk.content)
            )

        # 按1-3个字符长度拆分字符串形成流式输出的效果
        # start = 0
        # message_length = len(agent_message)
        # while start < message_length:
        #     # 随机生成1-3之间的长度
        #     chunk_length = random.randint(1, 3)
        #     # 防止最后一段超出字符串长度
        #     end = min(start + chunk_length, message_length)
        #     # 截取片段并返回
        #     yield return_chunk_format("response_chunk", agent_message[start:end])
        #     # 移动起始位置
        #     start = end

# Return 版本
#
# async def auto_build_agent(
#         agent_name: str,
#         agent_description: str,
#         llm_name: str,
#         tools_name: List[str] = [],
#         knowledges_name: List[str] = [],
#         mcp_servers_name: List[str] = [],
#         user_id: Optional[str]=None
# ):
#     """
#     自动构建智能体工具, 通过提取用户的输入信息来精准的帮助用户来快速创建一个智能体
#
#     params:
#         agent_name: 用户想要构建智能体的名称
#         agent_description: 对智能体功能、用途及特性的详细描述，帮助系统理解智能体的定位和作用范围
#         llm_name: 指定智能体所使用的大语言模型名称，需与系统支持的模型列表匹配，决定智能体的基础能力
#         tools_name: 智能体可调用的工具名称列表，用于扩展智能体的功能边界
#         knowledges_name: 智能体可访问的知识库名称列表，为智能体提供专业领域信息支持
#         mcp_servers_name: 智能体可连接的MCP服务名称列表，用于实现与外部系统的数据交互和功能调用
#     return:
#         返回创建智能体成功或者失败的信息
#     """
#     if len(agent_name) < 2 or len(agent_name) > 10:
#         error_message = f"智能体名称: {agent_name}, 不满足智能体名称要求的字符数限制, 字数要求大于等于2, 小于等于10"
#         logger.error(error_message)
#         return error_message
#
#     if len(agent_description) > 200:
#         error_message = f"智能体描述: {agent_description}, 不满足智能体描述要求的字符数限制, 字数要求小于200"
#         logger.error(error_message)
#         return error_message
#
#     try:
#         llm_id = await LLMService.get_llm_id_from_name(llm_name, user_id)
#
#         tool_ids = await ToolService.get_tool_ids_from_name(tools_name, user_id)
#
#         knowledge_ids = await KnowledgeService.get_knowledge_ids_from_name(knowledges_name, user_id)
#
#         mcp_server_ids = await MCPService.get_mcp_server_ids_from_name(mcp_servers_name, user_id)
#
#         await AgentService.create_agent(
#             name=agent_name,
#             description=agent_description,
#             llm_id=llm_id,
#             tool_ids=tool_ids,
#             mcp_ids=mcp_server_ids,
#             knowledge_ids=knowledge_ids,
#             user_id=user_id,
#             system_prompt="",
#             logo_url=app_settings.logo["agent_url"]
#         )
#         return f"""
#         您的智能体{agent_name}已经创建完毕, 请点击智能体页面进行查看
#         如果想要创建更多的智能体, 请跟我说哦~
#         """
#     except Exception as err:
#         return f"创建智能体失败,请根据该原因进行修改, 失败原因:{err}"



