from agentchat.database import AgentTable
from agentchat.database.dao.agent import AgentDao
from agentchat.database.dao.dialog import DialogDao
from agentchat.database.models.user import AdminUser, SystemUser
from agentchat.schema.agent import AgentCreateReq


class AgentService:

    # ---------- 内部工具 ----------

    @staticmethod
    def _to_dict_list(results):
        """
        将查询结果列表转换为字典列表，空列表返回 []
        """
        return [res.to_dict() for res in results] if results else []

    @classmethod
    async def _check_permission(
        cls,
        agent_id: str,
        user_id: str,
    ):
        """
        内部方法：检查用户对指定 agent 是否有权限
        管理员拥有所有权限
        """
        if user_id == AdminUser:
            return
        owner_id = await cls.get_agent_user_id(agent_id)
        if user_id != owner_id:
            raise ValueError("没有权限访问")

    # ---------- 写操作 ----------

    @classmethod
    async def create_agent(
        cls,
        login_user,
        req: AgentCreateReq,
    ):
        """
        创建新的 Agent
        login_user: 当前登录用户
        req: AgentCreateReq 请求数据
        """
        agent = AgentTable(
            **req.model_dump(),
            user_id=login_user.user_id,
        )
        return await AgentDao.create_agent(agent)

    @classmethod
    async def update_agent(
        cls,
        agent_id: str,
        update_values: dict,
        user_id: str,
    ):
        """
        更新指定 Agent 的信息
        agent_id: 要更新的 Agent ID
        update_values: 更新字段字典
        user_id: 操作用户
        """
        await cls._check_permission(agent_id, user_id)

        if not update_values:
            return

        await AgentDao.update_agent_by_id(
            agent_id=agent_id,
            update_values=update_values,
        )

    @classmethod
    async def delete_agent_by_id(
        cls,
        id: str,
    ):
        """
        删除指定 Agent 并删除其相关对话
        id: Agent ID
        """
        await AgentDao.delete_agent_by_id(
            id=id,
        )
        await DialogDao.delete_from_agent_id(
            id,
        )

    # ---------- 读操作 ----------

    @classmethod
    async def get_agent(
        cls,
    ):
        """
        查询所有 Agent
        返回字典列表
        """
        results = await AgentDao.get_agent()
        return cls._to_dict_list(results)

    @classmethod
    async def get_agent_user_id(
        cls,
        agent_id: str,
    ):
        """
        获取指定 Agent 的所属用户 ID
        agent_id: Agent ID
        """
        agent = await AgentDao.get_agent_user_id(
            agent_id=agent_id,
        )
        return agent.user_id

    @classmethod
    async def verify_user_permission(
        cls,
        id,
        user_id,
        action: str = "update",
    ):
        """
        对外接口：验证用户是否有权限操作 Agent
        action 可扩展，例如 update / delete 等
        """
        await cls._check_permission(id, user_id)

    @classmethod
    async def search_agent_name(
        cls,
        name: str,
        user_id: str,
    ):
        """
        根据名称模糊查询 Agent
        name: 查询名称
        user_id: 当前用户
        返回字典列表
        """
        results = await AgentDao.search_agent_name(
            name=name,
            user_id=user_id,
        )
        return cls._to_dict_list(results)

    @classmethod
    async def check_repeat_name(
        cls,
        name: str,
        user_id: str,
    ):
        """
        检查当前用户是否存在重复 Agent 名称
        返回 True/False
        """
        result = await AgentDao.check_repeat_name(
            name=name,
            user_id=user_id,
        )
        return bool(result)

    @classmethod
    async def check_name_iscustom(
        cls,
        name: str,
    ):
        """
        判断 Agent 是否为自定义类型
        """
        agent = await AgentDao.select_agent_by_name(
            name,
        )
        return agent.is_custom if agent else False

    @classmethod
    async def get_personal_agent_by_user_id(
        cls,
        user_id: str,
    ):
        """
        查询指定用户的个人 Agent
        返回字典列表
        """
        results = await AgentDao.get_agent_by_user_id(
            user_id=user_id,
        )
        return cls._to_dict_list(results)

    @classmethod
    async def get_all_agent_by_user_id(
        cls,
        user_id: str,
    ):
        """
        查询指定用户和系统 Agent
        返回字典列表
        """
        system_results = await AgentDao.get_agent_by_user_id(
            user_id=SystemUser,
        )
        user_results = await AgentDao.get_agent_by_user_id(
            user_id=user_id,
        )
        return cls._to_dict_list(system_results + user_results)

    @classmethod
    async def select_agent_by_custom(
        cls,
        is_custom,
    ):
        """
        查询自定义或系统 Agent
        is_custom: True/False
        """
        results = await AgentDao.select_agent_by_custom(
            is_custom=is_custom,
        )
        return cls._to_dict_list(results)

    @classmethod
    async def select_agent_by_name(
        cls,
        name: str,
    ):
        """
        精确查询 Agent 名称
        返回字典列表
        """
        results = await AgentDao.select_agent_by_name(
            name,
        )
        return cls._to_dict_list(results)

    @classmethod
    async def select_agent_by_id(
        cls,
        agent_id: str,
    ):
        """
        查询指定 Agent ID
        返回字典或 None
        """
        agent = await AgentDao.select_agent_by_id(
            agent_id,
        )
        return agent.to_dict() if agent else None
