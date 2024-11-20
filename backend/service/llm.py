from database.models.llm import LLMTable
from database.models.user import AdminUser, SystemUser
from type.schemas import UnifiedResponseModel, resp_500, resp_200
from database.dao.llm import LLMDao
from loguru import logger

class LLMService:

    @classmethod
    def create_llm(cls, user_id: str, api_key: str, model: str,
                   base_url: str, provider: str):
        try:
            LLMDao.create_llm(base_url=base_url, api_key=api_key,
                              model=model, provider=provider, user_id=user_id)
            return resp_200()
        except Exception as err:
            logger.error(f'create llm appear Err: {err}')
            return resp_500()

    @classmethod
    def delete_llm(cls, user_id: str, llm_id: str):
        try:
            if user_id == AdminUser or  user_id == cls.get_user_id_by_llm(llm_id):
                LLMDao.delete_llm(llm_id=llm_id)
                return resp_200()
            else:
                logger.error(f'no permission exec')
                return resp_500()
        except Exception as err:
            logger.error(f'delete llm appear Err: {err}')
            return resp_500()


    @classmethod
    def get_user_id_by_llm(cls, llm_id: str):
        try:
            llm = LLMDao.get_user_id_by_llm(llm_id)
            return llm.user_id
        except Exception as err:
            logger.error(f'get user id by llm appear Err: {err}')
            return str(err)

    @classmethod
    def update_llm(cls, user_id: str, llm_id: str, model: str,
                   base_url: str, api_key: str, provider: str):
        try:
            if user_id == AdminUser or user_id == cls.get_user_id_by_llm(llm_id):
                LLMDao.update_llm(llm_id=llm_id, model=model,
                                  base_url=base_url, api_key=api_key, provider=provider)
                return resp_200()
            else:
                logger.error(f'no permission exec')
                return resp_500()
        except Exception as err:
            logger.error(f'update llm appear Err: {err}')
            return resp_500()

    @classmethod
    def get_personal_llm(cls, user_id: str):
        try:
            llm_data = LLMDao.get_llm_by_user(user_id)
            result = []
            for data in llm_data:
                result.append(data[0])
            return resp_200(data=result)
        except Exception as err:
            logger.error(f'get personal llm appear Err: {err}')
            return resp_500()

    @classmethod
    def get_visible_llm(cls, user_id: str):
        try:
            user_data = LLMDao.get_llm_by_user(user_id)
            system_data = LLMDao.get_llm_by_user(SystemUser)
            result = []
            for data in set(user_data + system_data):
                result.append(data[0])
            return resp_200(data=result)
        except Exception as err:
            logger.error(f'get visible llm appear Err: {err}')
            return resp_500()

    @classmethod
    def get_all_llm(cls):
        try:
            llm_data = LLMDao.get_all_llm()
            result = []
            for data in llm_data:
                result.append(data[0])
            return resp_200(data=result)
        except Exception as err:
            logger.error(f'get all llm appear Err: {err}')
            return resp_500()

    @classmethod
    def get_llm_by_id(cls, llm_id: str):
        try:
            llm = LLMDao.get_llm_by_id(llm_id)
            return llm
        except Exception as err:
            logger.error(f'get llm by id appear Err: {err}')
