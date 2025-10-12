from typing import List

from sqlmodel import select, update, and_, delete
from agentchat.database.session import session_getter, async_session_getter
from agentchat.database.models.workbench_session import WorkBenchSession


class WorkBenchSessionDao:

    @classmethod
    async def get_workbench_sessions(cls, user_id):
        async with async_session_getter() as session:
            statement = select(WorkBenchSession).where(WorkBenchSession.user_id == user_id)
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def create_workbench_session(cls, workbench_session: WorkBenchSession):
        async with async_session_getter() as session:
            session.add(workbench_session)
            await session.commit()
            await session.refresh(workbench_session)
        return workbench_session

    @classmethod
    async def delete_workbench_session(cls, session_ids: List[str], user_id):
        async with async_session_getter() as session:
            statement = delete(WorkBenchSession).where(and_(WorkBenchSession.session_id.in_(session_ids),
                                                            WorkBenchSession.user_id == user_id))
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def update_workbench_session_contexts(cls, session_id, session_context):
        async with async_session_getter() as session:
            workbench_session = await session.get(WorkBenchSession, session_id)
            workbench_session.contexts.append(session_context)
            await session.commit()
            await session.refresh(workbench_session)

        return workbench_session

    @classmethod
    async def get_workbench_session_from_id(cls, session_id):
        async with async_session_getter() as session:
            workbench_session = await session.get(WorkBenchSession, session_id)
            return workbench_session