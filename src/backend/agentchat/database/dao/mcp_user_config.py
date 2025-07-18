from datetime import datetime
from typing import Optional

from sqlmodel import Session, select, and_, update, desc, delete, or_
from agentchat.database import engine

from agentchat.database.models.mcp_user_config import MCPUserConfigTable


class MCPUserConfigDao:
    @classmethod
    async def create_mcp_user_config(cls, mcp_server_id: str, user_id: str, config: Optional[dict] = None):
        """
        创建一个新的MCP用户配置记录。
        :param mcp_server_id: MCP Server ID
        :param user_id: 用户ID
        :param config: 配置信息（可选）
        :return: None
        """
        with Session(engine) as session:
            mcp_user_config = MCPUserConfigTable(mcp_server_id=mcp_server_id, user_id=user_id, config=config)
            session.add(mcp_user_config)
            session.commit()

    @classmethod
    async def get_mcp_user_config_from_id(cls, config_id: str):
        """
        根据ID获取MCP用户配置记录。
        :param config_id: 配置记录ID
        :return: 查询结果
        """
        with Session(engine) as session:
            sql = select(MCPUserConfigTable).where(MCPUserConfigTable.id == config_id)
            results = session.exec(sql).first()
            return results

    @classmethod
    async def delete_mcp_user_config(cls, config_id: str):
        """
        删除指定ID的MCP用户配置记录。
        :param config_id: 配置记录ID
        :return: None
        """
        with Session(engine) as session:
            sql = delete(MCPUserConfigTable).where(MCPUserConfigTable.id == config_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def update_mcp_user_config(cls, config_id: str, mcp_server_id: Optional[str] = None,
                               user_id: Optional[str] = None, config: Optional[dict] = None):
        """
        更新MCP用户配置记录。
        :param config_id: 配置记录ID
        :param mcp_server_id: MCP Server ID（可选）
        :param user_id: 用户ID（可选）
        :param config: 配置信息（可选）
        :return: None
        """
        with Session(engine) as session:
            update_values = {}
            if mcp_server_id:
                update_values["mcp_server_id"] = mcp_server_id
            if user_id:
                update_values["user_id"] = user_id
            if config:
                update_values["config"] = config

            sql = update(MCPUserConfigTable).where(MCPUserConfigTable.id == config_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    async def get_mcp_user_configs(cls, user_id: str, mcp_server_id: str):
        """
        获取MCP用户配置记录列表。
        :param user_id: 用户ID
        :param mcp_server_id: MCP Server ID
        :return: 查询结果
        """
        with Session(engine) as session:
            sql = select(MCPUserConfigTable)
            sql = sql.where(
                and_(MCPUserConfigTable.user_id == user_id, MCPUserConfigTable.mcp_server_id == mcp_server_id))
            results = session.exec(sql)
            return results.first()
