from loguru import logger
from config.service_config import SUCCESS_RESP, FAIL_RESP
from database.dao.knowledge import KnowledgeDao


class KnowledgeService:

    @classmethod
    def create_knowledge(cls, knowledge_name, knowledge_desc, user_id, oss_object_name):
        try:
            KnowledgeDao.create_knowledge(knowledge_name, knowledge_desc, user_id, oss_object_name)
            logger.info(f'Success Create knowledge')
            return SUCCESS_RESP
        except Exception as err:
            logger.error(f'Create Knowledge Error: {err}')
            return FAIL_RESP

    @classmethod
    def select_knowledge(cls, user_id):
        try:
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
    def delete_knowledge(cls, knowledge_id):
        try:
            KnowledgeDao.delete_knowledge_by_id(knowledge_id)
            logger.info(f'Success Delete Knowledge ID: {knowledge_id}')
            return SUCCESS_RESP
        except Exception as err:
            logger.error(f'Delete Knowledge By ID Error: {err}')
            return FAIL_RESP

    @classmethod
    def update_knowledge(cls, knowledge_id, knowledge_name, knowledge_desc):
        try:
            KnowledgeDao.update_knowledge_by_id(knowledge_id, knowledge_name, knowledge_desc)
            logger.info(f'Success Update Knowledge ID: {knowledge_id}')
            return SUCCESS_RESP
        except Exception as err:
            logger.error(f'Update Knowledge Error: {err}')
            return FAIL_RESP