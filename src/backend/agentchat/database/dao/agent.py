from datetime import datetime

from typing import List
from agentchat.database.models.agent import AgentTable
from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete
from agentchat.utils.helpers import delete_img
from agentchat.database import engine

class AgentDao:

    @classmethod
    def _get_agent_sql(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                       llm_id: str, tool_ids: List[str], is_custom: bool, use_embedding: bool, mcp_ids: List[str]):
        agent = AgentTable(name=name,
                           logo_url=logo_url,
                           user_id=user_id,
                           llm_id=llm_id,
                           tool_ids=tool_ids,
                           description=description,
                           knowledge_ids=knowledge_ids,
                           is_custom=is_custom,
                           mcp_ids=mcp_ids,
                           use_embedding=use_embedding)
        return agent

    @classmethod
    def create_agent(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                     llm_id: str, tool_ids: List[str], is_custom: bool, use_embedding: bool, mcp_ids: List[str]):
        with Session(engine) as session:
            session.add(cls._get_agent_sql(name, description, logo_url, user_id, knowledge_ids, llm_id, tool_ids, is_custom, use_embedding, mcp_ids))
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
    # def select_agent_by_type(cls, schema: str):
    #     with Session(engine) as session:
    #         sql = select(AgentTable).where(AgentTable.schema == schema)
    #         result = session.exec(sql).all()
    #         return result

    @classmethod
    def select_agent_by_custom(cls, is_custom: bool):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.is_custom == is_custom)
            result = session.exec(sql).all()
            return result

    # @classmethod
    # def get_agent_by_name_type(cls, name: str, schema: str):
    #     with Session(engine) as session:
    #         sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.schema == schema))
    #         result = session.exec(sql).all()
    #         return result

    @classmethod
    def delete_agent_by_id(cls, id: str):
        with Session(engine) as session:
            sql = delete(AgentTable).where(AgentTable.id == id)
            session.exec(sql)
            session.commit()

    @classmethod
    def _get_logo_by_id(cls, id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            result = session.exec(sql).all()
            return result[0][0].logo_url

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
    def get_agent_by_user_id(cls, user_id: str):
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
    def update_agent_by_id(cls, id: str, name: str, description: str, knowledge_ids: List[str],
                           logo_url: str, llm_id: str, tool_ids: List[str], use_embedding: bool, mcp_ids: List[str]):
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
            if tool_ids is not None:
                update_values['tool_ids'] = tool_ids
            if knowledge_ids is not None:
                update_values['knowledge_ids'] = knowledge_ids
            if use_embedding:
                update_values['use_embedding'] = use_embedding
            if mcp_ids:
                update_values["mcp_ids"] = mcp_ids

            if logo_url is not None:
                # 删除agent的logo地址
                agent_logo = cls._get_logo_by_id(id)
                delete_img(logo_url=agent_logo)
                update_values['logo_url'] = logo_url

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
            # if schema is not None:
            #     agent.schema = schema
            # if code is not None:
            #     agent.code = code
            # if logo_url is not None:
            #     # 删除agent的logo地址
            #     delete_img(logo_url=logo_url)
            #     agent.logo_url = logo_url
            # agent.create_time = datetime.utcnow()
            #
            # session.add(agent)
            # session.commit()
            # session.refresh()


