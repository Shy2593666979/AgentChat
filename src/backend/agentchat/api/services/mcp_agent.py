from agentchat.database.dao.mcp_agent import MCPAgentDao
from agentchat.database.models.user import AdminUser, SystemUser
from loguru import logger
from typing import List
from agentchat.schema.schemas import resp_200, resp_500


class MCPAgentService:

    @classmethod
    def create_mcp_agent(cls, name: str, description: str, logo: str, user_id: str, knowledges_id: List[str],
                         llm_id: str, mcp_servers_id: List[str], enable_memory: bool, is_custom: bool = True):
        try:
            agent_id = MCPAgentDao.create_mcp_agent(name=name,
                                                    description=description,
                                                    logo=logo,
                                                    llm_id=llm_id,
                                                    mcp_servers_id=mcp_servers_id,
                                                    user_id=user_id,
                                                    knowledges_id=knowledges_id,
                                                    is_custom=is_custom,
                                                    enable_memory=enable_memory)
            return agent_id
        except Exception as err:
            logger.error(f"create agent is appear error: {err}")

    @classmethod
    def get_mcp_agent(cls):
        try:
            data = MCPAgentDao.get_mcp_agent()
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f"get agent is appear error: {err}")

    @classmethod
    def update_mcp_agent_by_id(cls, id: str, name: str, description: str, user_id: str,
                               logo: str, mcp_servers_id: List[str], knowledges_id: List[str], llm_id: str,
                               enable_memory: bool):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == cls.get_agent_user_id(agent_id=id):
                MCPAgentDao.update_mcp_agent_by_id(id=id,
                                                   name=name,
                                                   logo=logo,
                                                   description=description,
                                                   knowledges_id=knowledges_id,
                                                   mcp_servers_id=mcp_servers_id,
                                                   llm_id=llm_id,
                                                   enable_memory=enable_memory)
                return resp_200(message='update agent success')
            else:
                return resp_500(message='no permission exec')
        except Exception as err:
            logger.error(f"update agent by id appear error: {err}")

    @classmethod
    def get_mcp_agent_user_id(cls, agent_id: str):
        try:
            agent = MCPAgentDao.get_mcp_agent_user_id(agent_id=agent_id)
            return agent.user_id
        except Exception as err:
            logger.error(f'get agent user id Err: {err}')

    @classmethod
    def delete_mcp_agent_by_id(cls, id: str, user_id: int):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == cls.get_agent_user_id(agent_id=id):
                MCPAgentDao.delete_mcp_agent_by_id(id=id)
                return resp_200(message='delete success')
            else:
                return resp_500(message='no permission exec')
        except Exception as err:
            logger.error(f"delete agent by id appear: {err}")

    @classmethod
    def search_mcp_agent_name(cls, name: str, user_id: str):
        try:
            data = MCPAgentDao.search_mcp_agent_name(name=name, user_id=user_id)
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f"search agent name appear error: {err}")

    @classmethod
    def check_repeat_name(cls, name: str, user_id: str):
        try:
            result = MCPAgentDao.check_repeat_name(name=name, user_id=user_id)
            if len(result) != 0:
                return True
            else:
                return False
        except Exception as err:
            logger.error(f"check repeat agent name appear error: {err}")

    @classmethod
    def check_name_iscustom(cls, name: str):
        try:
            agent = MCPAgentDao.select_mcp_agent_by_name(name)
            return agent.is_custom
        except Exception as err:
            logger.error(f"get code by name is appear error: {err}")

    @classmethod
    def get_personal_mcp_agent_by_user(cls, user_id: int):
        try:
            data = MCPAgentDao.get_mcp_agent_by_user_id(user_id=user_id)
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f'get personal agent by user id Err: {err}')

    @classmethod
    def get_all_mcp_agent_by_user(cls, user_id: int):
        try:
            system_data = MCPAgentDao.get_mcp_agent_by_user_id(user_id=SystemUser)
            user_data = MCPAgentDao.get_mcp_agent_by_user_id(user_id=user_id)
            result = []
            for item in (system_data + user_data):
                result.append(item)
            return result
        except Exception as err:
            logger.error(f'get all agent by user id Err: {err}')

    @classmethod
    def select_mcp_agent_by_custom(cls, is_custom):
        try:
            data = MCPAgentDao.select_mcp_agent_by_custom(is_custom=is_custom)
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f"select agent by custom is appear error: {err}")

    @classmethod
    def select_mcp_agent_by_name(cls, name: str):
        try:
            data = MCPAgentDao.select_mcp_agent_by_name(name)
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f"select agent by name is appear error: {err}")

    @classmethod
    def select_mcp_agent_by_id(cls, agent_id: str):
        try:
            data = MCPAgentDao.select_mcp_agent_by_id(agent_id)
            return data
        except Exception as err:
            logger.error(f"select agent by id is appear error: {err}")
