import json
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import aiofiles
import yaml
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from agentchat.database import SystemUser, engine, ensure_database
from agentchat.database.dao.agent import AgentDao
from agentchat.database.dao.agent_skill import AgentSkillDao
from agentchat.database.dao.llm import LLMDao
from agentchat.database.dao.mcp_server import MCPServerDao
from agentchat.database.dao.tool import ToolDao
from agentchat.database.models.agent import AgentTable
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.database.models.tool import ToolTable
from agentchat.settings import app_settings
from agentchat.utils.helpers import get_provider_from_model

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


async def init_agentchat_system():
    """按依赖顺序准备系统模板，不访问远端 MCP、下载头像或调用模型。"""
    try:
        await init_database()
        model_id = await _init_default_llm()
        await _init_default_tools()
        await init_default_agent_skills()
        await _init_system_mcp_server()
        await _init_default_agents(model_id)
    except Exception:
        logger.exception("系统默认数据初始化失败")
        raise
    logger.success("系统默认数据已就绪")


async def init_database():
    """根据模型定义创建数据库及表，不执行旧库结构迁移。"""
    ensure_database()
    SQLModel.metadata.create_all(engine)
    logger.info("数据库表已就绪：{}", engine.dialect.name)


async def load_json(filename: str):
    """从固定配置目录读取文件，不依赖启动命令的工作目录。"""
    async with aiofiles.open(CONFIG_DIR / filename, "r", encoding="utf-8") as config_file:
        return json.loads(await config_file.read())


async def _init_default_llm() -> str:
    """创建或同步系统模型配置，返回默认智能体使用的模型 ID。"""
    settings = app_settings.multi_models.chat_model
    model = await LLMDao.select_first_llm()
    if model is None:
        await LLMDao.create_llm(
            user_id=SystemUser,
            model=settings.model_name,
            llm_type="LLM",
            api_key=settings.api_key,
            base_url=settings.base_url,
            provider=get_provider_from_model(settings.model_name),
        )
        model = await LLMDao.select_first_llm()
    elif settings.api_key and "**" in settings.api_key:
        # 配置中的掩码不能覆盖已保存的真实凭据。
        logger.warning("系统模型密钥为掩码，保留已保存配置")
    elif (
        model.model != settings.model_name
        or model.api_key != settings.api_key
        or model.base_url != settings.base_url
    ):
        await LLMDao.update_first_llm(
            llm_id=model.llm_id,
            model=settings.model_name,
            provider=get_provider_from_model(settings.model_name),
            api_key=settings.api_key,
            base_url=settings.base_url,
        )
    return model.llm_id


async def _init_default_tools():
    """补齐系统工具模板，保留已存在的模板内容。"""
    configs = await load_json("tool.json")
    existing = await ToolDao.get_tool_by_user_id(SystemUser)
    names = {tool.name for tool in existing}
    for config in configs:
        if config["name"] in names:
            continue
        await ToolDao.create_default_tool(
            ToolTable(**config, user_id=SystemUser, is_user_defined=False)
        )
        names.add(config["name"])


async def _init_default_agents(model_id: str):
    """按系统工具补齐默认智能体，不把个人工具作为初始化模板。"""
    tools = await ToolDao.get_tool_by_user_id(SystemUser)
    existing = await AgentDao.get_agent_by_user_id(SystemUser)
    bindings = {tuple(agent.tool_ids) for agent in existing}
    for tool in tools:
        if (tool.tool_id,) in bindings:
            continue
        await AgentDao.create_agent(
            AgentTable(
                name=f"{tool.display_name}助手",
                description=tool.description,
                logo_url=tool.logo_url,
                tool_ids=[tool.tool_id],
                user_id=SystemUser,
                is_custom=False,
                llm_id=model_id,
            )
        )
        bindings.add((tool.tool_id,))


async def _init_system_mcp_server():
    """从配置读取默认 MCP 名称和描述，只创建缺失的系统模板。"""
    configs = await load_json("mcp_server.json")
    # 在写入前检查完整配置，禁止缺失元数据时改为调用模型生成。
    for config in configs:
        for field in ("server_name", "mcp_as_tool_name", "description"):
            if not isinstance(config.get(field), str) or not config[field].strip():
                raise ValueError(f"默认 MCP 配置缺少有效的 {field}")

    existing = await MCPServerDao.get_mcp_servers_from_user(SystemUser)
    urls = {server.url for server in existing}
    for config in configs:
        if config["url"] in urls:
            continue
        await MCPServerDao.create_mcp_server(
            server_name=config["server_name"],
            mcp_as_tool_name=config["mcp_as_tool_name"],
            description=config["description"],
            user_id=SystemUser,
            user_name="system",
            url=config["url"],
            type=config["type"],
            config=config.get("config", {}),
            tools=config.get("tools", []),
            params=config.get("params") or [],
            imported_config=config.get("imported_config"),
            config_enabled=config.get("config_enabled", False),
            logo_url=config["logo_url"],
        )
        urls.add(config["url"])


def load_default_skill_configs(config_dir: Path = CONFIG_DIR) -> list[dict]:
    """把本地技能目录转成现有编辑器和子智能体使用的文件树。"""
    presets = json.loads((config_dir / "default_skills.json").read_text(encoding="utf-8"))
    if not isinstance(presets, list):
        raise ValueError("默认 Skill 配置必须是数组")
    skills_root = (config_dir / "skills").resolve()
    keys, tool_names = set(), set()
    results = []
    for preset in presets:
        key, tool_name = preset["key"], preset["as_tool_name"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) or len(key) > 64:
            raise ValueError("默认 Skill 标识不合法")
        if not re.fullmatch(r"[a-z][a-z0-9_]*_skill", tool_name) or len(tool_name) > 64:
            raise ValueError("默认 Skill 工具名称不合法")
        if key in keys or tool_name in tool_names:
            raise ValueError("默认 Skill 标识或工具名称重复")
        keys.add(key)
        tool_names.add(tool_name)
        skill_dir = skills_root / key
        if skill_dir.is_symlink() or not skill_dir.resolve().is_relative_to(skills_root):
            raise ValueError("技能目录不能指向配置目录外的文件")
        entrypoint = skill_dir / "SKILL.md"
        if entrypoint.is_symlink() or not entrypoint.resolve().is_relative_to(skill_dir.resolve()):
            raise ValueError("SKILL.md 不能指向技能目录外的文件")
        content = entrypoint.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.DOTALL)
        metadata = yaml.safe_load(match.group(1)) if match else None
        if not isinstance(metadata, dict) or metadata.get("name") != key:
            raise ValueError(f"{key} 的 SKILL.md 缺少正确的名称元数据")
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"{key} 的 SKILL.md 缺少描述")

        def folder_tree(directory: Path, virtual_path: str) -> dict:
            children = []
            for item in sorted(directory.iterdir(), key=lambda path: (not path.is_dir(), path.name)):
                # 配置只载入当前目录内的文本，不跟随符号链接，也不执行脚本。
                if item.is_symlink() or not item.resolve().is_relative_to(skill_dir.resolve()):
                    raise ValueError(f"技能资源路径越界：{item.name}")
                path = f"{virtual_path}/{item.name}"
                if item.is_dir():
                    children.append(folder_tree(item, path))
                else:
                    children.append(
                        {
                            "name": item.name,
                            "path": path,
                            "type": "file",
                            "content": item.read_text(encoding="utf-8"),
                        }
                    )
            return {
                "name": directory.name,
                "path": virtual_path,
                "type": "folder",
                "folder": children,
            }

        results.append(
            {
                "id": uuid5(NAMESPACE_URL, f"agentchat/default-skills/{key}").hex,
                "name": preset["name"],
                "description": description.strip(),
                "as_tool_name": tool_name,
                "user_id": SystemUser,
                "folder": folder_tree(skill_dir, f"/{key}"),
            }
        )
    return results


async def init_default_agent_skills(config_dir: Path = CONFIG_DIR) -> None:
    """启动时补齐默认技能；固定工具名称，不调用模型，也不覆盖已有编辑。"""
    # 先完整检查配置，避免错误配置造成部分技能入库。
    presets = load_default_skill_configs(config_dir)
    existing = await AgentSkillDao.get_agent_skills(SystemUser)
    tool_names = {skill.as_tool_name for skill in existing}
    added = 0
    for preset in presets:
        saved = await AgentSkillDao.get_agent_skill_by_id(preset["id"])
        if saved:
            if saved.user_id != SystemUser:
                raise ValueError("默认 Skill 的固定 ID 与用户记录冲突")
            continue
        # 相同工具标识只保留一个系统模板，避免重复创建。
        if preset["as_tool_name"] in tool_names:
            continue
        try:
            await AgentSkillDao.create_agent_skill(AgentSkill(**preset))
            added += 1
            tool_names.add(preset["as_tool_name"])
        except IntegrityError:
            # 多个后端进程同时启动时，固定主键避免重复创建。
            saved = await AgentSkillDao.get_agent_skill_by_id(preset["id"])
            if saved is None or saved.user_id != SystemUser:
                raise
    logger.info("默认 Skill 已加载，本次新增 {} 个", added)
