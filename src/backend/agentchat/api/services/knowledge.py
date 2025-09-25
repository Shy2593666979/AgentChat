from typing import List

from agentchat.database.dao.knowledge import KnowledgeDao
from agentchat.database.dao.knowledge_file import KnowledgeFileDao
from agentchat.database.models.user import AdminUser
from agentchat.utils.file_utils import format_file_size


class KnowledgeService:

    @classmethod
    async def create_knowledge(cls, knowledge_name, knowledge_desc, user_id):
        try:
            await KnowledgeDao.create_knowledge(knowledge_name, knowledge_desc, user_id)
        except Exception as err:
            raise ValueError(f'Create Knowledge Error: {err}')


    @classmethod
    async def select_knowledge(cls, user_id):
        try:
            # 如果是admin用户，显示全部
            if user_id == AdminUser:
                knowledges = await cls._select_all_knowledge()
            else:
                knowledges = await KnowledgeDao.get_knowledge_by_user(user_id)
                knowledges = [knowledge.to_dict() for knowledge in knowledges]
            for knowledge in knowledges:
                knowledge_files = await KnowledgeFileDao.select_knowledge_file(knowledge["id"])
                knowledge["count"] = len(knowledge_files)
                file_sizes = 0
                for file in knowledge_files:
                    file_sizes += file.file_size
                knowledge["file_size"] = format_file_size(file_sizes)
            return knowledges

        except Exception as err:
            raise ValueError(f'Select Knowledge By User Error: {err}')

    @classmethod
    async def _select_all_knowledge(cls):
        try:
            results = await KnowledgeDao.get_all_knowledge()
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f'Delete Knowledge By ID Error: {err}')

    @classmethod
    async def delete_knowledge(cls, knowledge_id):
        try:
            await KnowledgeDao.delete_knowledge_by_id(knowledge_id)
        except Exception as err:
            raise ValueError(f'Delete Knowledge By ID Error: {err}')

    @classmethod
    async def verify_user_permission(cls, knowledge_id, user_id):
        knowledge_user_id = await cls.select_user_by_id(knowledge_id)
        if user_id != knowledge_user_id and user_id != AdminUser:
            raise ValueError(f'没有权限访问')

    @classmethod
    async def update_knowledge(cls, knowledge_id, knowledge_name, knowledge_desc):
        try:
            await KnowledgeDao.update_knowledge_by_id(knowledge_id, knowledge_desc, knowledge_name)
        except Exception as err:
            raise ValueError(f'Update Knowledge Error: {err}')

    @classmethod
    async def select_user_by_id(cls, knowledge_id):
        try:
            knowledge = await KnowledgeDao.select_user_by_id(knowledge_id)
            return knowledge.user_id
        except Exception as err:
            raise ValueError(f'Select user id error :{err}')

    @classmethod
    async def get_knowledge_ids_from_name(cls, knowledges_name: List[str], user_id):
        try:
            knowledges = await KnowledgeDao.get_knowledge_ids_from_name(knowledges_name, user_id)
            return [knowledge.id for knowledge in knowledges]
        except Exception as err:
            raise ValueError(f"Get knowledges id form name error:{err}")

