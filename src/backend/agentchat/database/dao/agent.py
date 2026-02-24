from agentchat.database import SystemUser
from agentchat.database.models.agent import AgentTable
from sqlmodel import select, and_, update, desc, delete, or_

from agentchat.database.session import session_getter


class AgentDao:

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
            statement = select(AgentTable).order_by(desc(AgentTable.create_time))
            result = session.exec(statement).all()
            return result

    @classmethod
    async def select_agent_by_name(cls, name: str):
        with session_getter() as session:
            statement = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(statement).first()
            return result

    @classmethod
    async def get_agent_user_id(cls, agent_id: str):
        with session_getter() as session:
            statement = select(AgentTable).where(AgentTable.id == agent_id)
            agent = session.exec(statement).first()
            return agent

    @classmethod
    async def select_agent_by_custom(cls, is_custom: bool):
        with session_getter() as session:
            statement = select(AgentTable).where(AgentTable.is_custom == is_custom)
            result = session.exec(statement).all()
            return result

    @classmethod
    async def delete_agent_by_id(cls, id: str):
        with session_getter() as session:
            statement = delete(AgentTable).where(AgentTable.id == id)
            session.exec(statement)
            session.commit()

    @classmethod
    async def _get_logo_by_id(cls, id: str):
        with session_getter() as session:
            statement = select(AgentTable).where(AgentTable.id == id)
            result = session.exec(statement).all()
            return result[0][0].logo_url

    @classmethod
    async def check_repeat_name(cls, name: str, user_id: str):
        with session_getter() as session:
            statement = select(AgentTable).where(
                and_(
                    AgentTable.name == name,
                    AgentTable.user_id == user_id
                )
            )
            result = session.exec(statement).all()
            return result

    @classmethod
    async def search_agent_name(
        cls, 
        name: str, 
        user_id: str
    ):
        with session_getter() as session:
            statement = select(AgentTable).where(
                and_(
                    AgentTable.name.like(f'%{name}%'),
                    or_(
                        AgentTable.user_id == user_id,
                        AgentTable.user_id == SystemUser
                    )
                )
            )
            result = session.exec(statement).all()
            return result

    @classmethod
    async def get_agent_by_user_id(
        cls, 
        user_id: str
    ):
        with session_getter() as session:
            statement = select(AgentTable).where(AgentTable.user_id == user_id)
            result = session.exec(statement).all()
            return result

    @classmethod
    async def select_agent_by_id(
        cls, 
        agent_id
    ):
        with session_getter() as session:
            statement = select(AgentTable).where(AgentTable.id == agent_id)
            result = session.exec(statement).first()
            return result

    @classmethod
    async def update_agent_by_id(
        cls,
        agent_id: str,
        update_values: dict
    ):
        with session_getter() as session:
            statement = (
                update(AgentTable)
                .where(AgentTable.id == agent_id)
                .values(**update_values)
            )
            session.exec(statement)
            session.commit()
