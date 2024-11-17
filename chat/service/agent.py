from aiohttp.test_utils import REUSE_ADDRESS

from database import AgentTable
from database.dao.agent import AgentDao
from database.models.user import AdminUser, SystemUser
from loguru import logger

from test.test_tool import message
from type.schemas import resp_200, resp_500


class AgentService:

    @classmethod
    def create_agent(cls, name: str, description: str, logo: str, user_id: int,
                     parameter: str, type: str = "openai", code: str = "", is_custom: bool = True):
        try:
            agent_id = AgentDao.create_agent(name=name,
                                            description=description,
                                            logo=logo,
                                            parameter=parameter,
                                            type=type,
                                            code=code,
                                            user_id=user_id,
                                            is_custom=is_custom)
            return agent_id
        except Exception as err:
            logger.error(f"create agent is appear error: {err}")

    @classmethod
    def get_agent(cls):
        try:
            data = AgentDao.get_agent()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get agent is appear error: {err}")

    @classmethod
    def select_agent_by_type(cls, type: str):
        try:
            data = AgentDao.select_agent_by_type(type)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select agent by type is appear error: {err}")

    @classmethod
    def select_agent_by_custom(cls, is_custom):
        try:
            data = AgentDao.select_agent_by_custom(is_custom=is_custom)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select agent by custom is appear error: {err}")

    @classmethod
    def select_agent_by_name(cls, name: str):
        try:
            data = AgentDao.select_agent_by_name(name)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select agent by name is appear error: {err}")

    @classmethod
    def get_parameter_by_name(cls, name: str):
        try:
            data = AgentDao.select_agent_by_name(name)
            return data[0][0].parameter
        except Exception as err:
            logger.error(f"get parameter by name is appear error: {err}")

    @classmethod
    def get_code_by_name(cls, name: str):
        try:
            data = AgentDao.select_agent_by_name(name)
            return data[0][0].code
        except Exception as err:
            logger.error(f"get code by name is appear error: {err}")

    @classmethod
    def get_agent_by_name_type(cls, name: str, type: str = "openai"):
        try:
            data = AgentDao.get_agent_by_name_type(name=name, type=type)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get agent by name and type appear error: {err}")

    @classmethod
    def update_agent_by_id(cls, id: str, name: str, description: str, user_id: int, logo: str, parameter: str, code: str, type: str=None):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == cls.get_agent_user_id(agent_id=id):
                AgentDao.update_agent_by_id(id=id,
                                            name=name,
                                            logo=logo,
                                            type=type,
                                            description=description,
                                            parameter=parameter,
                                            code=code)
                return resp_200(message='update agent success')
            else:
                return resp_500(message='no permission exec')
        except Exception as err:
            logger.error(f"update agent by id appear error: {err}")

    @classmethod
    def get_agent_user_id(cls, agent_id: str):
        try:
            agent = AgentDao.get_agent_user_id(agent_id=agent_id)
            return agent.user_id
        except Exception as err:
            logger.error(f'get agent user id Err: {err}')

    @classmethod
    def delete_agent_by_id(cls, id: str, user_id: int):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == cls.get_agent_user_id(agent_id=id):
                AgentDao.delete_agent_by_id(id=id)
                return resp_200(message='delete success')
            else:
                return resp_500(message='no permission exec')
        except Exception as err:
            logger.error(f"delete agent by id appear: {err}")

    @classmethod
    def search_agent_name(cls, name: str, user_id: int):
        try:
            data = AgentDao.search_agent_name(name=name, user_id=user_id)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"search agent name appear error: {err}")

    @classmethod
    def check_repeat_name(cls, name: str):
        try:
            result = AgentDao.check_repeat_name(name=name)
            if len(result) != 0:
                return True
            else:
                return False
        except Exception as err:
            logger.error(f"check repeat agent name appear error: {err}")

    @classmethod
    def check_name_iscustom(cls, name: str):
        try:
            data = AgentDao.select_agent_by_name(name)
            return data[0][0].is_custom
        except Exception as err:
            logger.error(f"get code by name is appear error: {err}")

    @classmethod
    def get_personal_agent_by_user_id(cls, user_id: int):
        try:
            data = AgentDao.get_agent_by_user_id(user_id=user_id)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f'get personal agent by user id Err: {err}')

    @classmethod
    def get_all_agent_by_user_id(cls, user_id: int):
        try:
            system_data = AgentDao.get_agent_by_user_id(user_id=SystemUser)
            user_data = AgentDao.get_agent_by_user_id(user_id=user_id)
            result = []
            for item in set(system_data + user_data):
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f'get all agent by user id Err: {err}')