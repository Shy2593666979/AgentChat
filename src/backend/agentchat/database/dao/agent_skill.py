from typing import Sequence, List

from sqlmodel import delete, select
from agentchat.database.session import async_session_getter
from agentchat.database.models.agent_skill import AgentSkill


class AgentSkillDao:

    @classmethod
    async def create_agent_skill(cls, agent_skill: AgentSkill):
        async with async_session_getter() as session:
            session.add(agent_skill)
            await session.commit()
            await session.refresh(agent_skill)
            return agent_skill

    @classmethod
    async def delete_agent_skill(cls, agent_skill_id):
        async with async_session_getter() as session:
            statement = delete(AgentSkill).where(
                AgentSkill.id == agent_skill_id
            )
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def get_agent_skills(cls, user_id):
        async with async_session_getter() as session:
            statement = select(AgentSkill).where(
                AgentSkill.user_id == user_id
            )
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_agent_skill_by_id(cls, agent_skill_id) -> AgentSkill:
        async with async_session_getter() as session:
            statement = select(AgentSkill).where(
                AgentSkill.id == agent_skill_id
            )
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def get_agent_skills_by_ids(
        cls,
        agent_skill_ids: List[str],
    ) -> List[AgentSkill]:
        if not agent_skill_ids:
            return []

        async with async_session_getter() as session:
            statement = select(AgentSkill).where(
                AgentSkill.id.in_(agent_skill_ids)
            )
            result = await session.exec(statement)
            return result.all()


    @classmethod
    async def update_agent_skill(cls, agent_skill: AgentSkill):
        async with async_session_getter() as session:
            merged = await session.merge(agent_skill)
            await session.commit()
            await session.refresh(merged)
            return merged
