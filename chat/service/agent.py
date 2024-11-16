from database.dao.agent import AgentDao
from loguru import logger


class AgentService:

    @classmethod
    def create_agent(cls, name: str, description: str, logo: str, parameter: str, type: str = "openai", code: str = "",
                     isCustom: bool = True):
        try:
            agentId = AgentDao.create_agent(name=name,
                                            description=description,
                                            logo=logo,
                                            parameter=parameter,
                                            type=type,
                                            code=code,
                                            isCustom=isCustom)
            return agentId
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
    def select_agent_by_custom(cls, isCustom):
        try:
            data = AgentDao.select_agent_by_custom(isCustom=isCustom)
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
    def update_agent_by_id(cls, id: str, name: str, description: str, logo: str, parameter: str, code: str):
        try:
            AgentDao.update_agent_by_id(id=id,
                                        name=name,
                                        logo=logo,
                                        description=description,
                                        parameter=parameter,
                                        code=code)
        except Exception as err:
            logger.error(f"update agent by id appear error: {err}")

    @classmethod
    def delete_agent_by_id(cls, id: str):
        try:
            AgentDao.delete_agent_by_id(id=id)
        except Exception as err:
            logger.error(f"delete agent by id appear: {err}")

    @classmethod
    def search_agent_name(cls, name: str):
        try:
            data = AgentDao.search_agent_name(name=name)
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
            return data[0][0].isCustom
        except Exception as err:
            logger.error(f"get code by name is appear error: {err}")
