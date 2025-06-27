from datetime import datetime

from typing import List
from agentchat.database.models.agent import AgentTable
from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete
from agentchat.utils.helpers import delete_img
from agentchat.database import engine


class AgentDao:

    @classmethod
    async def _get_agent_sql(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                       llm_id: str, tool_ids: List[str], is_custom: bool, use_embedding: bool, mcp_ids: List[str],
                       system_prompt: str):
        agent = AgentTable(name=name, logo_url=logo_url, user_id=user_id, llm_id=llm_id,
                           tool_ids=tool_ids, description=description, mcp_ids=mcp_ids,
                           system_prompt=system_prompt, use_embedding=use_embedding, is_custom=is_custom)
        return agent

    @classmethod
    async def create_agent(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                     llm_id: str, tool_ids: List[str], is_custom: bool, use_embedding: bool, mcp_ids: List[str],
                     system_prompt: str):
        with Session(engine) as session:
            session.add(
                cls._get_agent_sql(name, description, logo_url, user_id, knowledge_ids, llm_id, tool_ids, is_custom,
                                   use_embedding, mcp_ids, system_prompt))
            session.commit()

    @classmethod
    async def get_agent(cls):
        with Session(engine) as session:
            sql = select(AgentTable).order_by(desc(AgentTable.create_time))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def select_agent_by_name(cls, name: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_agent_user_id(cls, agent_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == agent_id)
            agent = session.exec(sql).first()
            return agent

    # @classmethod
    # async def select_agent_by_type(cls, schema: str):
    #     with Session(engine) as session:
    #         sql = select(AgentTable).where(AgentTable.schema == schema)
    #         result = session.exec(sql).all()
    #         return result

    @classmethod
    async def select_agent_by_custom(cls, is_custom: bool):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.is_custom == is_custom)
            result = session.exec(sql).all()
            return result

    # @classmethod
    # async def get_agent_by_name_type(cls, name: str, schema: str):
    #     with Session(engine) as session:
    #         sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.schema == schema))
    #         result = session.exec(sql).all()
    #         return result

    @classmethod
    async def delete_agent_by_id(cls, id: str):
        with Session(engine) as session:
            sql = delete(AgentTable).where(AgentTable.id == id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def _get_logo_by_id(cls, id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            result = session.exec(sql).all()
            return result[0][0].logo_url

    @classmethod
    async def check_repeat_name(cls, name: str, user_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def search_agent_name(cls, name: str, user_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(and_(AgentTable.name.like(f'%{name}%'),
                                                AgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_agent_by_user_id(cls, user_id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def select_agent_by_id(cls, agent_id):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == agent_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    async def update_agent_by_id(cls, id: str, name: str, description: str, knowledge_ids: List[str],
                           logo_url: str, llm_id: str, tool_ids: List[str], use_embedding: bool, mcp_ids: List[str],
                           system_prompt):
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
            if system_prompt:
                update_values["system_prompt"] = system_prompt
            if logo_url is not None:
                update_values['logo_url'] = logo_url

            sql = update(AgentTable).where(AgentTable.id == id).values(**update_values)
            session.exec(sql)
            session.commit()
