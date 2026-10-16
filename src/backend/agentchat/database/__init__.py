from loguru import logger
from sqlmodel import SQLModel

from agentchat.database.models.agent import AgentTable
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.database.models.conversation import ConversationTable
from agentchat.database.models.history import HistoryTable
from agentchat.database.models.knowledge import KnowledgeTable
from agentchat.database.models.knowledge_file import KnowledgeFileTable
from agentchat.database.models.llm import LLMTable
from agentchat.database.models.mcp_server import MCPServerStdioTable, MCPServerTable
from agentchat.database.models.mcp_user_config import MCPUserConfigTable
from agentchat.database.models.memory_history import MemoryHistoryTable
from agentchat.database.models.message import MessageDownTable, MessageLikeTable
from agentchat.database.models.register_mcp import RegisterMcpServer
from agentchat.database.models.register_mcp_tool import RegisterMcpTool
from agentchat.database.models.register_task import RegisterMcpTask
from agentchat.database.models.role import Role
from agentchat.database.models.tool import ToolTable
from agentchat.database.models.usage_stats import UsageStats
from agentchat.database.models.user import SystemUser
from agentchat.database.models.user_role import UserRole
from agentchat.database.models.workspace_session import WorkSpaceSession
from agentchat.settings import app_settings

from .connection import (
    configure_sqlite_timestamps,
    create_database_engines,
    resolve_database_urls,
)
from .connection import (
    ensure_database as _ensure_database,
)

database_urls = resolve_database_urls(app_settings.database or app_settings.mysql)
if database_urls.dialect == "sqlite":
    configure_sqlite_timestamps(SQLModel.metadata)
engine, async_engine = create_database_engines(database_urls)


def ensure_database(endpoint: str | None = None) -> None:
    urls = (
        resolve_database_urls(
            {
                "url": endpoint,
            }
        )
        if endpoint
        else database_urls
    )
    _ensure_database(urls.sync)


def ensure_mysql_database(endpoint: str | None = None) -> None:
    """Compatibility alias for older callers; selection is now URL-based."""
    ensure_database(endpoint)
