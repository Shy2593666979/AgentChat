from datetime import datetime

from sqlmodel import Session, select, and_, update, desc, delete, or_
from agentchat.database.session import session_getter

from agentchat.database.models.mcp_server import MCPServerStdioTable, MCPServerTable


class MCPServerStdioDao:

    @classmethod
    def create_mcp_server(cls, mcp_server_path: str, mcp_server_command: str,
                          user_id: str, name: str, mcp_server_env: str):
        with session_getter() as session:
            mcp_server = MCPServerStdioTable(user_id=user_id,
                                        name=name,
                                        mcp_server_env=mcp_server_env,
                                        mcp_server_path=mcp_server_path,
                                        mcp_server_command=mcp_server_command)
            session.add(mcp_server)
            session.commit()

    @classmethod
    def get_mcp_servers(cls, user_id):
        with session_getter() as session:
            if user_id:
                sql = select(MCPServerStdioTable).where(MCPServerStdioTable.user_id == user_id)
            else:
                sql = select(MCPServerStdioTable)
            mcp_servers = session.exec(sql).all()
            return mcp_servers

    @classmethod
    def delete_mcp_server(cls, mcp_server_id):
        with session_getter() as session:
            sql = delete(MCPServerStdioTable).where(MCPServerStdioTable.mcp_server_id == mcp_server_id)
            session.exec(sql)
            session.commit()

    @classmethod
    def update_mcp_server(cls, mcp_server_id: str, mcp_server_path: str,
                          mcp_server_command: str, name: str, mcp_server_env: str):
        with session_getter() as session:
            update_values = {}
            if mcp_server_env:
                update_values["mcp_server_env"] = mcp_server_env
            if mcp_server_path:
                update_values["mcp_server_path"] = mcp_server_path
            if mcp_server_command:
                update_values["mcp_server_command"] = mcp_server_command
            if name:
                update_values["name"] = name

            sql = update(MCPServerStdioTable).where(MCPServerStdioTable.mcp_server_id == mcp_server_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    def get_mcp_server_by_id(cls, mcp_server_id):
        with session_getter() as session:
            sql = select(MCPServerStdioTable).where(MCPServerStdioTable.mcp_server_id == mcp_server_id)
            mcp_server = session.exec(sql).all()
            return mcp_server