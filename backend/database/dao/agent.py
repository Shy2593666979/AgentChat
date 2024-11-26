from datetime import datetime

from typing import List
from database.models.agent import AgentTable
from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete
from utils.helpers import delete_img
from database import engine

class AgentDao:

    @classmethod
    def _get_agent_sql(cls, name: str, description: str, logo: str, user_id: str,
                       llm_id: str, tool_id: List[str], is_custom: bool, embedding_id: str):
        agent = AgentTable(name=name,
                           logo=logo,
                           user_id=user_id,
                           llm_id=llm_id,
                           tool_id=tool_id,
                           description=description,
                           is_custom=is_custom,
                           embedding_id=embedding_id)
        return agent

    @classmethod
    def create_agent(cls, name: str, description: str, logo: str, user_id: str,
                     llm_id: str, tool_id: List[str], is_custom: bool, embedding_id: str):
        with Session(engine) as session:
            session.add(cls._get_agent_sql(name, description, logo, user_id, llm_id, tool_id, is_custom, embedding_id))
            session.commit()

    @classmethod
    def get_agent(cls):
        with Session(engine) as session:
            sql = select(AgentTable).order_by(desc(AgentTable.create_time))
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_name(cls, name: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_agent_user_id(cls, agent_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id==agent_id)
            agent = session.exec(sql).first()
            return agent

    # @classmethod
    # def select_agent_by_type(cls, type: str):
    #     with Session(engine) as session:
    #         sql = select(AgentTable).where(AgentTable.type == type)
    #         result = session.exec(sql).all()
    #         return result

    @classmethod
    def select_agent_by_custom(cls, is_custom: bool):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.is_custom == is_custom)
            result = session.exec(sql).all()
            return result

    # @classmethod
    # def get_agent_by_name_type(cls, name: str, type: str):
    #     with Session(engine) as session:
    #         sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.type == type))
    #         result = session.exec(sql).all()
    #         return result

    @classmethod
    def delete_agent_by_id(cls, id: str):
        with Session(engine) as session:
            sql = delete(AgentTable).where(AgentTable.id == id)
            session.exec(sql)
            # 删除agent的logo地址
            agent_logo = cls._get_logo_by_id(id)
            delete_img(logo=agent_logo)
            session.commit()

    @classmethod
    def _get_logo_by_id(cls, id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            result = session.exec(sql).all()
            return result[0][0].logo

    @classmethod
    def check_repeat_name(cls, name: str, user_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    def search_agent_name(cls, name: str, user_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(and_(AgentTable.name.like(f'%{name}%'),
                                                AgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_agent_by_user_id(cls, user_id: int):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_id(cls, agent_id):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == agent_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    def update_agent_by_id(cls, id: str, name: str, description: str,
                           logo: str, llm_id: str, tool_id: List[str], embedding_id: str):
        with Session(engine) as session:
            # 构建 update 语句
            update_values = {
                'create_time': datetime.utcnow()
            }
            if name is not None:
                update_values['name'] = name
            if description is not None:
                update_values['description'] = description
            if llm_id is not None:
                update_values['llm_id'] = llm_id
            if tool_id is not None:
                update_values['tool_id'] = tool_id

            if logo is not None:
                # 删除agent的logo地址
                agent_logo = cls._get_logo_by_id(id)
                delete_img(logo=agent_logo)
                update_values['logo'] = logo

            sql = update(AgentTable).where(AgentTable.id == id).values(**update_values)
            session.exec(sql)
            session.commit()
            # sql = select(AgentTable).where(AgentTable.id == id)
            # agent = session.exec(sql).one()
            #
            # if name is not None:
            #     agent.name = name
            # if description is not None:
            #     agent.description = description
            # if parameter is not None:
            #     agent.parameter = parameter
            # if type is not None:
            #     agent.type = type
            # if code is not None:
            #     agent.code = code
            # if logo is not None:
            #     # 删除agent的logo地址
            #     delete_img(logo=logo)
            #     agent.logo = logo
            # agent.create_time = datetime.utcnow()
            #
            # session.add(agent)
            # session.commit()
            # session.refresh()


