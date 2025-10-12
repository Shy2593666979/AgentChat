from typing import List

from agentchat.database.dao.workbench_session import WorkBenchSession, WorkBenchSessionDao
from agentchat.database.models.workbench_session import WorkBenchSessionCreate


class WorkBenchSessionService:

    @classmethod
    async def create_workbench_session(cls, session_create: WorkBenchSessionCreate):
        workbench_session = WorkBenchSession(**session_create.model_dump())
        return await WorkBenchSessionDao.create_workbench_session(workbench_session)

    @classmethod
    async def get_workbench_sessions(cls, user_id):
        results = await WorkBenchSessionDao.get_workbench_sessions(user_id)
        return [result.to_dict() for result in results]

    @classmethod
    async def delete_workbench_session(cls, session_ids, user_id):
        await WorkBenchSessionDao.delete_workbench_session(session_ids, user_id)

    @classmethod
    async def update_workbench_session_contexts(cls, session_id, session_context):
        return await WorkBenchSessionDao.update_workbench_session_contexts(session_id, session_context)

    @classmethod
    async def get_workbench_session_from_id(cls, session_id, user_id):
        result = await WorkBenchSessionDao.get_workbench_session_from_id(session_id)
        if result.user_id != user_id:
            raise ValueError("无权限操作该工作台会话")
        return result.to_dict()

    @classmethod
    async def generate_session_title(cls, user_query):
        pass