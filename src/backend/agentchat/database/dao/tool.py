from datetime import datetime

from agentchat.database.models.tool import ToolTable
from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete, or_
from typing import List
from agentchat.database import engine


class ToolDao:

    @classmethod
    async def _get_tool(cls, zh_name: str, en_name: str,
                        user_id: str, description: str, logo_url: str):
        tool = ToolTable(zh_name=zh_name, en_name=en_name, logo_url=logo_url,
                         user_id=user_id, description=description)
        return tool

    @classmethod
    async def create_tool(cls, zh_name: str, en_name: str,
                          user_id: str, description: str, logo_url: str):
        tool = await cls._get_tool(zh_name=zh_name, en_name=en_name, logo_url=logo_url,
                                   user_id=user_id, description=description)

        with Session(engine) as session:
            session.add(tool)
            session.commit()

    @classmethod
    async def delete_tool_by_id(cls, tool_id: str):
        with Session(engine) as session:
            sql = delete(ToolTable).where(ToolTable.tool_id == tool_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def update_tool_by_id(cls, tool_id: str, zh_name: str, en_name: str,
                                description: str, logo_url: str):
        with Session(engine) as session:
            update_values = {
                'create_time': datetime.utcnow()
            }
            if zh_name:
                update_values['zh_name'] = zh_name
            if en_name:
                update_values['en_name'] = en_name
            if description:
                update_values['description'] = description
            if logo_url:
                update_values['logo_url'] = logo_url

            sql = update(ToolTable).where(ToolTable.tool_id == tool_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    async def get_tool_by_user_id(cls, user_id: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_tool_name_by_id(cls, tool_id: List[str]):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.tool_id.in_(tool_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_all_tools(cls):
        with Session(engine) as session:
            sql = select(ToolTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_tool_by_id(cls, tool_id: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.tool_id == tool_id)
            tool = session.exec(sql).first()
            return tool

    @classmethod
    async def get_id_by_tool_name(cls, tool_name, user_id):
        with Session(engine) as session:
            sql = select(ToolTable).where(and_(ToolTable.en_name == tool_name,
                                               or_(ToolTable.user_id == user_id,
                                                   ToolTable.user_id == '0')))
            tool = session.exec(sql).first()
            return tool
