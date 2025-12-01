from datetime import datetime

from sqlmodel import Session, select, update, desc, delete, or_, func, and_
from agentchat.database.session import session_getter
from agentchat.database.models.mcp_server import MCPServerStdioTable, MCPServerTable


class MCPServerDao:
    @classmethod
    async def create_mcp_server(cls, server_name: str, user_id: str, user_name: str, mcp_as_tool_name: str, description: str,
                                url: str, type: str, config: dict, tools: list, params: dict, config_enabled: bool, logo_url):
        with session_getter() as session:
            mcp_server = MCPServerTable(server_name=server_name, user_id=user_id, logo_url=logo_url,
                                        user_name=user_name, url=url, type=type, config=config,
                                        tools=tools, params=params, config_enabled=config_enabled,
                                        mcp_as_tool_name=mcp_as_tool_name, description=description)
            session.add(mcp_server)
            session.commit()

    @classmethod
    async def get_mcp_server_from_id(cls, mcp_server_id):
        with session_getter() as session:
            sql = select(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id)
            results = session.exec(sql).first()
            return results

    @classmethod
    async def delete_mcp_server(cls, mcp_server_id):
        with session_getter() as session:
            sql = delete(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def update_mcp_server(cls, mcp_server_id: str, server_name: str, mcp_as_tool_name: str, description: str,
                                url: str, type: str, config: dict, tools: list, params: dict, logo_url: str):
        with session_getter() as session:
            update_values = {}
            if server_name:
                update_values["server_name"] = server_name
            if url:
                update_values["url"] = url
            if type:
                update_values["type"] = type
            if config:
                update_values["config"] = config
            if tools:
                update_values["tools"] = tools
            if params:
                update_values["params"] = params
            if logo_url:
                update_values["logo_url"] = logo_url
            if mcp_as_tool_name:
                update_values["mcp_as_tool_name"] = mcp_as_tool_name
            if description:
                update_values["description"] = description

            sql = update(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id).values(**update_values)
            session.exec(sql)
            session.commit()

    # 检查更新时间是否超过7天
    @classmethod
    async def get_first_mcp_server(cls):
        with session_getter() as session:
            statement = select(MCPServerTable)
            server = session.exec(statement).first()
            return server

    @classmethod
    async def get_server_from_tool_name(cls, tool_name):
        with session_getter() as session:
            sql = select(MCPServerTable).where(func.json_contains(MCPServerTable.tools, func.json_array(tool_name)))
            results = session.exec(sql).first()
            return results

    @classmethod
    async def get_mcp_servers_from_user(cls, user_id):
        with session_getter() as session:
            sql = select(MCPServerTable).where(MCPServerTable.user_id == user_id)
            results = session.exec(sql)
            return results.all()

    @classmethod
    async def get_all_mcp_servers(cls):
        with session_getter() as session:
            sql = select(MCPServerTable)
            results = session.exec(sql)
            return results.all()

    @classmethod
    async def get_mcp_server_ids_from_name(cls, mcp_servers_name, user_id):
        with session_getter() as session:
            sql = select(MCPServerTable).where(and_(MCPServerTable.server_name.in_(mcp_servers_name),
                                                    MCPServerTable.user_id == user_id))
            result = session.exec(sql)
            return result.all()