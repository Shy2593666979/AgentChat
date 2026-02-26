import asyncio
from typing import List, Union

from agentchat.database import SystemUser, ToolTable
from agentchat.database.models.user import AdminUser
from agentchat.database.dao.tool import ToolDao


class ToolService:

    @classmethod
    async def create_default_tool(
        cls,
        default_tool: ToolTable
    ):
        result = await ToolDao.create_default_tool(default_tool)
        return result

    @classmethod
    async def create_user_defined_tool(
        cls,
        tool: ToolTable
    ):
        result = await ToolDao.create_user_defined_tool(tool)
        return result

    @classmethod
    async def delete_user_defined_tool(
        cls,
        tool_id: str
    ):
        await ToolDao.delete_user_defined_tool(tool_id=tool_id)

    @classmethod
    async def verify_user_permission(
        cls,
        tool_id: str,
        user_id: str,
    ):
        authorized_user_id = await cls._get_user_by_tool_id(tool_id)

        # 权限检查：如果不是管理员 且 不是工具所属用户，则拒绝访问
        if user_id != AdminUser and user_id != authorized_user_id:
            raise ValueError("没有权限访问该资源")

    @classmethod
    async def get_personal_tool_by_user(
        cls,
        user_id: str
    ):
        try:
            personal_results = await ToolDao.get_tool_by_user_id(user_id=user_id)
            return [res.to_dict() for res in personal_results]
        except Exception as err:
            raise ValueError(f'Get Tool By User Id Appear Error: {err}')

    @classmethod
    async def get_visible_tool_by_user(
        cls,
        user_id: str
    ):
        try:
            personal_results = await ToolDao.get_tool_by_user_id(user_id=user_id)
            system_results = await ToolDao.get_tool_by_user_id(user_id=SystemUser)
            return [res.to_dict() for res in personal_results + system_results]
        except Exception as err:
            raise ValueError(f'Get All Tool By User Appear Error: {err}')

    @classmethod
    async def get_all_tools(
        cls,
        user_id: str
    ) -> list[dict]:
        """获取用户工具 + 系统默认工具"""
        if user_id == SystemUser:
            tools = await ToolDao.get_all_tools(SystemUser)
            return [tool.to_dict() for tool in tools]

        tools, default_tools = await asyncio.gather(
            ToolDao.get_all_tools(user_id),
            ToolDao.get_all_tools(SystemUser),
        )

        # 转成 list 再合并
        return [tool.to_dict() for tool in [*tools, *default_tools]]

    @classmethod
    async def get_tool_name_by_id(
        cls,
        tool_id: Union[List[str], str]
    ):
        try:
            tool_ids = [tool_id] if isinstance(tool_id, str) else tool_id
            tools = await ToolDao.get_tool_name_by_id(tool_id=tool_ids)
            result = [tool.name for tool in tools]
            return result
        except Exception as err:
            raise ValueError(f'Get Tool name by Id appear Err: {err}')

    @classmethod
    async def get_tools_from_id(
        cls,
        tool_ids: Union[List[str], str]
    ) -> List[ToolTable]:
        tool_ids = [tool_ids] if isinstance(tool_ids, str) else tool_ids
        tools = await ToolDao.get_tool_name_by_id(tool_id=tool_ids)
        return tools

    @classmethod
    async def _get_user_by_tool_id(
        cls,
        tool_id: str
    ):
        try:
            tool = await ToolDao.get_tool_by_id(tool_id=tool_id)
            return tool.tool_id
        except Exception as err:
            raise ValueError(f'Get user by tool Id appear Error: {err}')

    @classmethod
    async def get_tools_data(cls):
        try:
            tools = await ToolDao.get_all_tools(SystemUser)
            return [tool.to_dict() for tool in tools]
        except Exception as err:
            raise ValueError(f'Get tools data appear Error: {err}')

    @classmethod
    async def get_id_by_tool_name(
        cls,
        tool_name: str,
        user_id: str
    ):
        try:
            tool = await ToolDao.get_id_by_tool_name(tool_name, user_id)
            return tool.tool_id
        except Exception as err:
            raise ValueError(f'Get Id by tool name appear Error: {err}')


    @classmethod
    async def get_tool_ids_from_name(
        cls,
        tool_names: List[str],
        user_id
    ):
        try:
            tools = await ToolDao.get_tool_ids_from_name(tool_names, user_id)
            # 加上系统自带的
            tools.extend(await ToolDao.get_tool_ids_from_name(tool_names, SystemUser))
            return [tool.tool_id for tool in tools]
        except Exception as err:
            raise ValueError(f'Get Tool ID tool name appear Error: {err}')

    @classmethod
    async def get_user_defined_tools(cls, user_id):
        tools = await ToolDao.get_user_defined_tools(user_id)
        return [tool.to_dict() for tool in tools]

    @classmethod
    async def update_user_defined_tool(cls, tool_id, update_values):
        await ToolDao.update_user_defined_tool(tool_id, update_values)