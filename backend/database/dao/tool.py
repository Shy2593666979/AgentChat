from datetime import datetime

from database.models.tool import ToolTable
from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete, or_
from typing import List
from database import engine

class ToolDao:

    @classmethod
    def _get_tool(cls, zh_name: str, en_name: str,
                  user_id: str, description: str,):
        tool = ToolTable(zh_name=zh_name, en_name=en_name,
                         user_id=user_id,description=description)
        return tool

    @classmethod
    def create_tool(cls, zh_name: str, en_name: str,
                    user_id: str, description: str,):
        tool = cls._get_tool(zh_name=zh_name, en_name=en_name,
                             user_id=user_id, description=description)

        with Session(engine) as session:
            session.add(tool)
            session.commit()

    @classmethod
    def delete_tool_by_id(cls, tool_id: str):
        with Session(engine) as session:
            sql = delete(ToolTable).where(ToolTable.tool_id == tool_id)
            session.exec(sql)
            session.commit()

    @classmethod
    def update_tool_by_id(cls, tool_id: str, zh_name: str=None, en_name: str=None, description: str=None):
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

            sql = update(ToolTable).where(ToolTable.tool_id == tool_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    def get_tool_by_user_id(cls, user_id: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_tool_name_by_id(cls, tool_id: List[str]):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.tool_id.in_(tool_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_all_tools(cls):
        with Session(engine) as session:
            sql = select(ToolTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_tool_by_id(cls, tool_id: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.tool_id==tool_id)
            tool = session.exec(sql).first()
            return tool

    @classmethod
    def get_id_by_tool_name(cls, tool_name, user_id):
        with Session(engine) as session:
            sql = select(ToolTable).where(and_(ToolTable.en_name == tool_name,
                                               or_(ToolTable.user_id == user_id,
                                                   ToolTable.user_id == '0')))
            tool = session.exec(sql).first()
            return tool