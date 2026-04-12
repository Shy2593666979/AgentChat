import json
import asyncio
import httpx
import aiofiles
from loguru import logger
from sqlmodel import SQLModel

from agentchat.database import engine, SystemUser, ensure_mysql_database, AgentTable, ToolTable
from agentchat.api.services.agent import AgentService
from agentchat.api.services.llm import LLMService
from agentchat.api.services.tool import ToolService
from agentchat.api.services.mcp_server import MCPService
from agentchat.database.dao.agent import AgentDao
from agentchat.database.models.user import AdminUser
from agentchat.prompts.mcp import McpAsToolPrompt
from agentchat.schemas.mcp import MCPResponseFormat
from agentchat.services.mcp.manager import MCPManager
from agentchat.services.storage import storage_client
from agentchat.settings import app_settings
from agentchat.utils.convert import convert_mcp_config
from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.utils.helpers import get_provider_from_model

async def init_agentchat_system():
    """
    agentchat 启动入口（推荐用于每次服务启动）

    功能：
    - 初始化数据库（幂等）
    - 检查系统是否已初始化
    - 自动选择：
        - 未初始化 → 全量初始化
        - 已初始化 → 增量更新（LLM + MCP）
    """
    await init_database()

    try:
        agents = await AgentService.get_agent()

        # 首次启动
        if not agents:
            logger.info("First-time setup: initializing agentchat system...")
            await asyncio.gather(
                _init_default_tools(),
                _init_default_llms(),
                _init_system_mcp_server(),
                upload_user_avatars_storage(),
            )
            await _init_default_agents()
            logger.success("Initialized agentchat successfully")
            return

        logger.info(f"Existing system detected ({len(agents)} agents), updating config...")

        await asyncio.gather(
            _update_exist_llm(),
            _update_mcp_server_into_mysql(True),
        )
        logger.success("agentchat runtime ready")
    except Exception as err:
        logger.error(f" agentchat init failed: {err}")

async def init_database():
    """
    初始化数据库：
    - 创建数据库（如果不存在）
    - 创建所有表结构
    """
    try:
        ensure_mysql_database()
        SQLModel.metadata.create_all(engine)
        logger.success("MySQL tables are ready")
    except Exception as err:
        logger.error(f"Create MySQL Table Error: {err}")

async def load_json(path: str):
    """
    异步读取 JSON 文件（避免阻塞事件循环）

    Args:
        path: 文件路径

    Returns:
        dict/list: JSON 数据
    """
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return json.loads(await f.read())

async def _init_default_tools():
    """初始化默认工具"""
    tools = await load_json("./agentchat/config/tool.json")

    await asyncio.gather(*[
        ToolService.create_default_tool(
            ToolTable(
                **tool,
                user_id=SystemUser,
                is_user_defined=False
            )
        )
        for tool in tools
    ])

    logger.success("Default tools initialized")


async def _update_exist_llm():
    """
    更新已存在的 LLM 配置

    逻辑：
    - 获取当前系统已有 LLM
    - 对比配置（model / base_url / api_key）
    - 若无变化 → 跳过
    - 若 API Key 是掩码（包含 **）→ 跳过（防止覆盖真实 key）
    """
    settings = app_settings.multi_models.conversation_model

    api_key = settings.api_key
    base_url = settings.base_url
    model = settings.model_name
    provider = get_provider_from_model(model)

    llm = await LLMService.select_first_llm()

    if not llm:
        # 如果数据库还没有 LLM，直接初始化
        await _init_default_llms()
        return

    # 是否需要更新
    needs_update = not (
        llm.base_url == base_url and
        llm.model == model and
        llm.api_key == api_key
    )

    if not needs_update:
        logger.info("LLM config unchanged, skip update")
        return

    # 防止用掩码覆盖真实 key
    if api_key and "**" in api_key:
        logger.warning("Masked API key detected, skip update")
        return

    await LLMService.update_first_llm(
        llm_id=llm.llm_id,
        model=model,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
    )

    logger.success("LLM config updated")

async def _init_default_llms():
    """初始化默认 LLM"""
    settings = app_settings.multi_models.conversation_model

    await LLMService.create_llm(
        user_id=SystemUser,
        model=settings.model_name,
        llm_type="LLM",
        api_key=settings.api_key,
        base_url=settings.base_url,
        provider=get_provider_from_model(settings.model_name)
    )

    logger.success("Default LLM initialized")

async def _init_default_agents():
    """
    初始化默认 Agent
    - 每个 Tool 对应一个 Agent
    - 并发创建
    """
    llm = await LLMService.get_one_llm()
    tools = await ToolService.get_tools_data()

    tasks = []

    for tool in tools:
        tool["name"] = tool["display_name"] + "助手"

        agent = AgentTable(
            **ToolTable(**tool).model_dump(exclude={"user_id", "tool_id"}),
            tool_ids=[tool["tool_id"]],
            user_id=SystemUser,
            is_custom=False,
            llm_id=llm.get("llm_id")
        )

        tasks.append(AgentDao.create_agent(agent))

    await asyncio.gather(*tasks)

    logger.success("Default agents initialized")

async def _init_system_mcp_server():
    """
    初始化 MCP Server（仅首次）
    """
    try:
        existing = await MCPService.get_all_servers(SystemUser)

        if not existing:
            await _update_mcp_server_into_mysql(False)

        logger.success("MCP servers initialized")

    except Exception as err:
        logger.error(f"MCP init failed: {err}")


async def _update_mcp_server_into_mysql(has_mcp_server: bool):
    """
    同步 MCP Server 到数据库（核心逻辑）

    Args:
        has_mcp_server:
            True = 更新模式
            False = 初始化模式
    """
    if has_mcp_server:
        if not await MCPService.mcp_server_need_update():
            return

        servers = await MCPService.get_all_servers(AdminUser)
        logger.info("Updating MCP servers...")
    else:
        servers = await load_json("./agentchat/config/mcp_server.json")

    servers_info = [
        {
            "type": s["type"],
            "url": s["url"],
            "server_name": s["server_name"]
        }
        for s in servers
    ]

    mcp_manager = MCPManager(convert_mcp_config(servers_info))
    servers_params = await mcp_manager.show_mcp_tools()

    semaphore = asyncio.Semaphore(5)

    async def build_meta(server_name, params):
        """
        构建 MCP Tool 元信息（调用 LLM）
        """
        async with semaphore:
            agent = StructuredResponseAgent(MCPResponseFormat)

            result = agent.get_structured_response(
                McpAsToolPrompt.format(
                    tools_info=json.dumps(params, indent=2)
                )
            )
            return server_name, params, result

    tasks = [
        build_meta(name, params)
        for name, params in servers_params.items()
    ]

    results = await asyncio.gather(*tasks)

    for server_name, params, structured in results:
        server = next((s for s in servers if s["server_name"] == server_name), None)

        tools_name = [t["name"] for t in params]

        if has_mcp_server:
            await MCPService.update_mcp_server(
                server_id=server["mcp_server_id"],
                update_data={
                    "tools": tools_name,
                    "params": params,
                    "mcp_as_tool_name": structured.mcp_as_tool_name,
                    "description": structured.description
                }
            )
        else:
            await MCPService.create_mcp_server(
                server_name=server_name,
                user_id=SystemUser,
                user_name="Admin",
                url=server["url"],
                type=server["type"],
                config=server["config"],
                tools=tools_name,
                params=params,
                config_enabled=server["config_enabled"],
                logo_url=server["logo_url"],
                mcp_as_tool_name=structured.mcp_as_tool_name,
                description=structured.description,
            )

async def upload_user_avatars_storage():
    """上传默认用户头像到存储"""
    if storage_client.list_files_in_folder("icons/user"):
        return

    avatars = await load_json("./agentchat/config/avatars.json")

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [
            _download_and_upload(client, url)
            for url in avatars["avatars"]
        ]
        await asyncio.gather(*tasks)

    logger.success("User avatars uploaded")


async def _download_and_upload(client, url):
    """下载图片并上传到存储"""
    resp = await client.get(url)
    file_name = url.split("/")[-1]

    storage_client.upload_file(
        f"icons/user/{file_name}",
        resp.content
    )