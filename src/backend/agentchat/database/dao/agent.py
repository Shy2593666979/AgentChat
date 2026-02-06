from datetime import datetime

from typing import List
from agentchat.database.models.agent import AgentTable
from sqlmodel import Session, select, and_, update, desc, delete
from agentchat.database.session import session_getter


class AgentDao:

    @classmethod
    async def _get_agent_sql(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                             llm_id: str, tool_ids: List[str], is_custom: bool, enable_memory: bool, mcp_ids: List[str],
                             system_prompt: str):
        agent = AgentTable(name=name, logo_url=logo_url, user_id=user_id, llm_id=llm_id,
                           tool_ids=tool_ids, description=description, mcp_ids=mcp_ids,
                           system_prompt=system_prompt, enable_memory=enable_memory, is_custom=is_custom)
        return agent

    @classmethod
    async def create_agent(
            cls,
            agent: AgentTable
    ):
        with session_getter() as session:
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    @classmethod
    async def get_agent(cls):
        with session_getter() as session:
            sql = select(AgentTable).order_by(desc(AgentTable.create_time))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def select_agent_by_name(cls, name: str):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(sql).first()
            return result

    @classmethod
    async def get_agent_user_id(cls, agent_id: str):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.id == agent_id)
            agent = session.exec(sql).first()
            return agent

    @classmethod
    async def select_agent_by_custom(cls, is_custom: bool):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.is_custom == is_custom)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def delete_agent_by_id(cls, id: str):
        with session_getter() as session:
            sql = delete(AgentTable).where(AgentTable.id == id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def _get_logo_by_id(cls, id: str):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            result = session.exec(sql).all()
            return result[0][0].logo_url

    @classmethod
    async def check_repeat_name(cls, name: str, user_id: str):
        with session_getter() as session:
            sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def search_agent_name(cls, name: str, user_id: str):
        with session_getter() as session:
            sql = select(AgentTable).where(and_(AgentTable.name.like(f'%{name}%'),
                                                AgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_agent_by_user_id(cls, user_id: str):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def select_agent_by_id(cls, agent_id):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.id == agent_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    async def update_agent_by_id(
            cls,
            agent_id: str,
            update_values: dict
    ):
        with session_getter() as session:
            sql = (
                update(AgentTable)
                .where(AgentTable.id == agent_id)
                .values(**update_values)
            )
            session.exec(sql)
            session.commit()
