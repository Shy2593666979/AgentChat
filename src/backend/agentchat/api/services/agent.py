from agentchat.database.dao.agent import AgentDao
from agentchat.database.dao.dialog import DialogDao
from agentchat.database.models.user import AdminUser, SystemUser
from loguru import logger
from typing import List
from agentchat.schema.schemas import resp_200, resp_500


class AgentService:

    @classmethod
    async def create_agent(cls, name: str, description: str, logo_url: str, user_id: str, knowledge_ids: List[str],
                           llm_id: str, tool_ids: List[str], mcp_ids: List[str], system_prompt: str,
                           enable_memory: bool = False, is_custom: bool = True):
        try:
            await AgentDao.create_agent(name=name, description=description, logo_url=logo_url,
                                        llm_id=llm_id, tool_ids=tool_ids, user_id=user_id,
                                        knowledge_ids=knowledge_ids, is_custom=is_custom,
                                        enable_memory=enable_memory, mcp_ids=mcp_ids, system_prompt=system_prompt)
        except Exception as err:
            raise ValueError(f"Create Agent Appear Error: {err}")

    @classmethod
    async def get_agent(cls):
        try:
            results = await AgentDao.get_agent()
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get Agent Appear Error: {err}")

    @classmethod
    async def update_agent_by_id(cls, id: str, name: str, description: str, user_id: str,
                                 logo_url: str, tool_ids: List[str], knowledge_ids: List[str], llm_id: str,
                                 enable_memory: bool, mcp_ids: List[str], system_prompt: str):
        try:
            # 需要判断是否有权限，管理员随意
            if user_id == AdminUser or user_id == await cls.get_agent_user_id(agent_id=id):
                await AgentDao.update_agent_by_id(id=id,
                                                  name=name,
                                                  logo_url=logo_url,
                                                  description=description,
                                                  knowledge_ids=knowledge_ids,
                                                  tool_ids=tool_ids,
                                                  llm_id=llm_id,
                                                  mcp_ids=mcp_ids,
                                                  enable_memory=enable_memory,
                                                  system_prompt=system_prompt)
            else:
                raise ValueError("No Permission Exec")
        except Exception as err:
            raise ValueError(f"Update Agent By Id Appear Error: {err}")

    @classmethod
    async def get_agent_user_id(cls, agent_id: str):
        try:
            agent = await AgentDao.get_agent_user_id(agent_id=agent_id)
            return agent.user_id
        except Exception as err:
            raise ValueError(f"Get Agent User Id Error: {err}")

    @classmethod
    async def verify_user_permission(cls, id, user_id, action: str="update"):
        if user_id == AdminUser or user_id == await cls.get_agent_user_id(agent_id=id):
            pass
        else:
            raise ValueError(f"没有权限访问")

    @classmethod
    async def delete_agent_by_id(cls, id: str):
        try:
            await AgentDao.delete_agent_by_id(id=id)
            await DialogDao.delete_from_agent_id(id)
        except Exception as err:
            raise ValueError(f"Delete Agent By Id Appear Error: {err}")

    @classmethod
    async def search_agent_name(cls, name: str, user_id: str):
        try:
            results = await AgentDao.search_agent_name(name=name, user_id=user_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Search Agent Name Appear Error: {err}")

    @classmethod
    async def check_repeat_name(cls, name: str, user_id: str):
        try:
            result = await AgentDao.check_repeat_name(name=name, user_id=user_id)
            if len(result) != 0:
                return True
            else:
                return False
        except Exception as err:
            raise ValueError(f"Check Repeat Agent Name Appear Error: {err}")

    @classmethod
    async def check_name_iscustom(cls, name: str):
        try:
            agent = await AgentDao.select_agent_by_name(name)
            return agent.is_custom
        except Exception as err:
            raise ValueError(f"Get Code by Name Appear Error: {err}")

    @classmethod
    async def get_personal_agent_by_user_id(cls, user_id: str):
        try:
            results = await AgentDao.get_agent_by_user_id(user_id=user_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get Personal Agent By User Id Error: {err}")

    @classmethod
    async def get_all_agent_by_user_id(cls, user_id: str):
        try:
            system_results = await AgentDao.get_agent_by_user_id(user_id=SystemUser)
            user_results = await AgentDao.get_agent_by_user_id(user_id=user_id)
            return [res.to_dict() for res in system_results + user_results]
        except Exception as err:
            raise ValueError(f"Get All Agent By User Id Error: {err}")

    @classmethod
    async def select_agent_by_custom(cls, is_custom):
        try:
            results = await AgentDao.select_agent_by_custom(is_custom=is_custom)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Select Agent By Custom Appear Error: {err}")

    @classmethod
    async def select_agent_by_name(cls, name: str):
        try:
            results = await AgentDao.select_agent_by_name(name)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Select Agent By Name Appear Error: {err}")

    @classmethod
    async def select_agent_by_id(cls, agent_id: str):
        try:
            agent = await AgentDao.select_agent_by_id(agent_id)
            return agent.to_dict() if agent else None
        except Exception as err:
            raise ValueError(f"Select Agent By Id Appear Error: {err}")
