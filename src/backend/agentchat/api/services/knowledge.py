from loguru import logger
from agentchat.config.service_config import SUCCESS_RESP, FAIL_RESP
from agentchat.database.dao.knowledge import KnowledgeDao
from agentchat.database.models.user import AdminUser


class KnowledgeService:

    @classmethod
    async def create_knowledge(cls, knowledge_name, knowledge_desc, user_id):
        try:
            KnowledgeDao.create_knowledge(knowledge_name, knowledge_desc, user_id)
            logger.info(f'Success Create knowledge')
            return SUCCESS_RESP
        except Exception as err:
            logger.error(f'Create Knowledge Error: {err}')
            return FAIL_RESP

    @classmethod
    async def select_knowledge(cls, user_id):
        try:
            # 如果是admin用户，显示全部
            if user_id == AdminUser:
                return await cls._select_all_knowledge()

            datas = KnowledgeDao.get_knowledge_by_user(user_id)
            result = []
            for data in datas:
                result.append(data[0])
            logger.info('Success Select All knowledges')
            return SUCCESS_RESP, result
        except Exception as err:
            logger.error(f'Select Knowledge By User Error: {err}')
            return FAIL_RESP, None

    @classmethod
    async def _select_all_knowledge(cls):
        try:
            datas = KnowledgeDao.get_all_knowledge()
            result = []
            for data in datas:
                result.append(data[0])
            return result
        except Exception as err:
            logger.error(f'Delete Knowledge By ID Error: {err}')

    @classmethod
    async def delete_knowledge(cls, knowledge_id, user_id):
        try:
            knowledge_user_id = await cls.select_user_by_id(knowledge_id)
            if user_id != knowledge_user_id and user_id != AdminUser:
                raise ValueError(f'User id: {user_id} update knowledge, but no permission')

            KnowledgeDao.delete_knowledge_by_id(knowledge_id)
            logger.info(f'Success Delete Knowledge ID: {knowledge_id}')
            return SUCCESS_RESP
        except Exception as err:
            logger.error(f'Delete Knowledge By ID Error: {err}')
            return FAIL_RESP

    @classmethod
    async def update_knowledge(cls, knowledge_id, knowledge_name, knowledge_desc, user_id):
        try:
            knowledge_user_id = await cls.select_user_by_id(knowledge_id)
            if user_id != knowledge_user_id and user_id != AdminUser:
                raise ValueError(f'User id: {user_id} update knowledge, but no permission')

            KnowledgeDao.update_knowledge_by_id(knowledge_id, knowledge_name, knowledge_desc)
            logger.info(f'Success Update Knowledge ID: {knowledge_id}')
            return SUCCESS_RESP
        except Exception as err:
            logger.error(f'Update Knowledge Error: {err}')
            return FAIL_RESP

    @classmethod
    async def select_user_by_id(cls, knowledge_id):
        try:
            knowledge = KnowledgeDao.select_user_by_id(knowledge_id)
            return knowledge.user_id
        except Exception as err:
            logger.error(f'select user id error :{err}')

