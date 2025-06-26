from agentchat.database.dao.agent import AgentDao
from agentchat.database.models.user import AdminUser, SystemUser
from loguru import logger
from typing import List
from agentchat.schema.schemas import resp_200, resp_500


class AgentService:

    @classmethod
    def create_agent(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                     llm_id: str, tool_ids: List[str], mcp_ids: List[str], use_embedding: bool = False, is_custom: bool = True):
        try:
            agent_id = AgentDao.create_agent(name=name,
                                             description=description,
                                             logo_url=logo_url,
                                             llm_id=llm_id,
                                             tool_ids=tool_ids,
                                             user_id=user_id,
                                             knowledge_ids=knowledge_ids,
                                             is_custom=is_custom,
                                             use_embedding=use_embedding,
                                             mcp_ids=mcp_ids)
            return agent_id
        except Exception as err:
            logger.error(f"create agent is appear error: {err}")
            raise ValueError(str(err))

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
            raise ValueError(str(err))

    @classmethod
    def update_agent_by_id(cls, id: str, name: str, description: str, user_id: str,
                           logo_url: str, tool_ids: List[str], knowledge_ids: List[str], llm_id: str, use_embedding: bool,
                           mcp_ids: List[str]):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == cls.get_agent_user_id(agent_id=id):
                AgentDao.update_agent_by_id(id=id,
                                            name=name,
                                            logo_url=logo_url,
                                            description=description,
                                            knowledge_ids=knowledge_ids,
                                            tool_ids=tool_ids,
                                            llm_id=llm_id,
                                            mcp_ids=mcp_ids,
                                            use_embedding=use_embedding)
                return resp_200(message="update agent success")
            else:
                return resp_500(message="no permission exec")
        except Exception as err:
            logger.error(f"update agent by id appear error: {err}")
            return resp_500(message=str(err))

    @classmethod
    def get_agent_user_id(cls, agent_id: str):
        try:
            agent = AgentDao.get_agent_user_id(agent_id=agent_id)
            return agent.user_id
        except Exception as err:
            logger.error(f"get agent user id Err: {err}")
            raise ValueError(str(err))

    @classmethod
    def delete_agent_by_id(cls, id: str, user_id: str):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == cls.get_agent_user_id(agent_id=id):
                AgentDao.delete_agent_by_id(id=id)
                return resp_200(message="delete success")
            else:
                return resp_500(message="no permission exec")
        except Exception as err:
            logger.error(f"delete agent by id appear: {err}")
            return resp_500(message=str(err))

    @classmethod
    def search_agent_name(cls, name: str, user_id: str):
        try:
            data = AgentDao.search_agent_name(name=name, user_id=user_id)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"search agent name appear error: {err}")
            raise ValueError(str(err))

    @classmethod
    def check_repeat_name(cls, name: str, user_id: str):
        try:
            result = AgentDao.check_repeat_name(name=name, user_id=user_id)
            if len(result) != 0:
                return True
            else:
                return False
        except Exception as err:
            logger.error(f"check repeat agent name appear error: {err}")
            raise ValueError(str(err))

    @classmethod
    def check_name_iscustom(cls, name: str):
        try:
            data = AgentDao.select_agent_by_name(name)
            return data[0][0].is_custom
        except Exception as err:
            logger.error(f"get code by name is appear error: {err}")
            raise ValueError(str(err))

    @classmethod
    def get_personal_agent_by_user_id(cls, user_id: str):
        try:
            data = AgentDao.get_agent_by_user_id(user_id=user_id)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get personal agent by user id Err: {err}")
            raise ValueError(str(err))

    @classmethod
    def get_all_agent_by_user_id(cls, user_id: str):
        try:
            system_data = AgentDao.get_agent_by_user_id(user_id=SystemUser)
            user_data = AgentDao.get_agent_by_user_id(user_id=user_id)
            result = []
            for item in (system_data + user_data):
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get all agent by user id Err: {err}")
            raise ValueError(str(err))

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
            raise ValueError(str(err))

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
            raise ValueError(str(err))

    @classmethod
    def select_agent_by_id(cls, agent_id: str):
        try:
            data = AgentDao.select_agent_by_id(agent_id)
            return data

        except Exception as err:
            logger.error(f"select agent by id is appear error: {err}")
            raise ValueError(str(err))

    # @classmethod
    # def get_parameter_by_name(cls, name: str):
    #     try:
    #         data = AgentDao.select_agent_by_name(name)
    #         return data[0][0].parameter
    #     except Exception as err:
    #         logger.error(f"get parameter by name is appear error: {err}")

    # @classmethod
    # def get_code_by_name(cls, name: str):
    #     try:
    #         data = AgentDao.select_agent_by_name(name)
    #         return data[0][0].code
    #     except Exception as err:
    #         logger.error(f"get code by name is appear error: {err}")

    # @classmethod
    # def get_agent_by_name_type(cls, name: str, schema: str = "openai"):
    #     try:
    #         data = AgentDao.get_agent_by_name_type(name=name, schema=schema)
    #         result = []
    #         for item in data:
    #             result.append(item[0])
    #         return result
    #     except Exception as err:
    #         logger.error(f"get agent by name and schema appear error: {err}")

    # @classmethod
    # def select_agent_by_type(cls, schema: str):
    #     try:
    #         data = AgentDao.select_agent_by_type(schema)
    #         result = []
    #         for item in data:
    #             result.append(item[0])
    #         return result
    #     except Exception as err:
    #         logger.error(f"select agent by schema is appear error: {err}")
