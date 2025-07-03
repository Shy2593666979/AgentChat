from datetime import datetime

from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete, or_
from agentchat.database import engine

from agentchat.database.models.mcp_server import MCPServerStdioTable, MCPServerTable


class MCPServerDao:
    @classmethod
    def create_mcp_server(cls, mcp_server_name: str, user_id: str, user_name: str,
                          url: str, type: str, config: dict, tools: str, params: dict, config_enabled: bool):
        with Session(engine) as session:
            mcp_server = MCPServerTable(mcp_server_name=mcp_server_name, user_id=user_id,
                                        user_name=user_name, url=url, type=type, config=config,
                                        tools=tools, params=params, config_enabled=config_enabled)
            session.add(mcp_server)
            session.commit()


    @classmethod
    def get_mcp_server_from_id(cls, mcp_server_id):
        with Session(engine) as session:
            sql = select(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id)
            results = session.exec(sql).all()
            return results

    @classmethod
    def delete_mcp_server(cls, mcp_server_id):
        with Session(engine) as session:
            sql = delete(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id)
            session.exec(sql)
            session.commit()

    @classmethod
    def update_mcp_server(cls, mcp_server_id: str, mcp_server_name: str,
                          url: str, type: str, config: dict, tools: str, params: dict):
        with Session(engine) as session:
            update_values = {
                'update_time': datetime.utcnow()
            }
            if mcp_server_name:
                update_values["mcp_server_name"] = mcp_server_name
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

            sql = update(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    def get_server_from_tool_name(cls, tool_name):
        with Session(engine) as session:
            sql = select(MCPServerTable).where(MCPServerTable.tools.contains(tool_name))
            results = session.exec(sql).all()
            return results


    @classmethod
    def get_mcp_servers(cls, user_id):
        with Session(engine) as session:
            sql = select(MCPServerTable).where(MCPServerTable.user_id == user_id)
            results = session.exec(sql)
            return results.all()