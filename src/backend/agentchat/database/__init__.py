from loguru import logger
from sqlmodel import SQLModel, create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from agentchat.database.models.agent import AgentTable
from agentchat.database.models.history import HistoryTable
from agentchat.database.models.memory_history import MemoryHistoryTable
from agentchat.database.models.user import SystemUser
from agentchat.database.models.knowledge import KnowledgeTable
from agentchat.database.models.knowledge_file import KnowledgeFileTable
from agentchat.database.models.tool import ToolTable
from agentchat.database.models.dialog import DialogTable
from agentchat.database.models.mcp_server import MCPServerTable, MCPServerStdioTable
from agentchat.database.models.mcp_user_config import MCPUserConfigTable
from agentchat.database.models.mcp_agent import MCPAgentTable
from agentchat.database.models.user_role import UserRole
from agentchat.database.models.llm import LLMTable
from agentchat.database.models.message import MessageDownTable, MessageLikeTable
from agentchat.database.models.role import Role
from agentchat.database.models.workspace_session import WorkSpaceSession
from agentchat.database.models.usage_stats import UsageStats
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.settings import app_settings


engine = create_engine(
    url=app_settings.mysql.get('endpoint'),
    pool_pre_ping=True, # 连接前检查其有效性
    pool_recycle=3600, # 每隔1小时进行重连一次
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET SESSION time_zone = '+08:00'"
    }
)

async_engine = create_async_engine(
    url=app_settings.mysql.get('async_endpoint'),
    pool_pre_ping=True,  # 连接前检查其有效性
    pool_recycle=3600,  # 每隔1小时进行重连一次
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET SESSION time_zone = '+08:00'"
    }
)


def ensure_mysql_database(endpoint: str=None) -> None:
    """
    Ensure MySQL database exists.
    This function is safe to call on every startup.
    """
    from urllib.parse import urlparse, urlunparse

    if not endpoint:
        endpoint = app_settings.mysql.get('endpoint')
    parsed = urlparse(endpoint)

    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError("MySQL endpoint must include database name")

    bootstrap_url = urlunparse((
        "mysql+pymysql",
        f"{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 3306}",
        "/",
        "",
        "",
        ""
    ))

    logger.info(f"Checking MySQL database `{database}`")

    engine = create_engine(
        bootstrap_url,
        isolation_level="AUTOCOMMIT",
        connect_args={
            "charset": "utf8mb4",
            "init_command": "SET SESSION time_zone = '+08:00'"
        }
    )

    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"""
                    CREATE DATABASE IF NOT EXISTS `{database}`
                    DEFAULT CHARACTER SET utf8mb4
                    COLLATE utf8mb4_unicode_ci
                    """
                )
            )
        logger.success(f"MySQL database `{database}` is ready")
    finally:
        engine.dispose()
