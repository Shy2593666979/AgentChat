from datetime import datetime

from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete, or_
from database import engine

from database.models.mcp_server import MCPServerTable


class MCPServerDao:

    @classmethod
    def create_mcp_server(cls, mcp_server_path: str, mcp_server_command: str,
                          user_id: str, name: str, mcp_server_env: str):
        with Session(engine) as session:
            mcp_server = MCPServerTable(user_id=user_id,
                                        name=name,
                                        mcp_server_env=mcp_server_env,
                                        mcp_server_path=mcp_server_path,
                                        mcp_server_command=mcp_server_command)
            session.add(mcp_server)
            session.commit()

    @classmethod
    def get_mcp_servers(cls, user_id):
        with Session(engine) as session:
            if user_id:
                sql = select(MCPServerTable).where(MCPServerTable.user_id == user_id)
            else:
                sql = select(MCPServerTable)
            mcp_servers = session.exec(sql).all()
            return mcp_servers

    @classmethod
    def delete_mcp_server(cls, mcp_server_id):
        with Session(engine) as session:
            sql = delete(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id)
            session.exec(sql)
            session.commit()

    @classmethod
    def update_mcp_server(cls, mcp_server_id: str, mcp_server_path: str,
                          mcp_server_command: str, name: str, mcp_server_env: str):
        with Session(engine) as session:
            update_values = {
                'create_time': datetime.utcnow()
            }
            if mcp_server_env:
                update_values["mcp_server_env"] = mcp_server_env
            if mcp_server_path:
                update_values["mcp_server_path"] = mcp_server_path
            if mcp_server_command:
                update_values["mcp_server_command"] = mcp_server_command
            if name:
                update_values["name"] = name

            sql = update(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    def get_mcp_server_by_id(cls, mcp_server_id):
        with Session(engine) as session:
            sql = select(MCPServerTable).where(MCPServerTable.mcp_server_id == mcp_server_id)
            mcp_server = session.exec(sql).first()
            return mcp_server
