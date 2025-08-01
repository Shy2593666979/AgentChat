from agentchat.database.models.user import AdminUser
from agentchat.database.dao.tool import ToolDao
from typing import List, Union
from agentchat.schema.schemas import resp_200, resp_500
from loguru import logger


class ToolService:

    @classmethod
    async def create_tool(cls, user_id: str, zh_name: str, en_name: str, description: str, logo_url: str):
        try:
            await ToolDao.create_tool(user_id=user_id, zh_name=zh_name, logo_url=logo_url,
                                      en_name=en_name, description=description)
        except Exception as err:
            raise ValueError(f'Create Tool Appear Error: {err}')

    @classmethod
    async def delete_tool(cls, tool_id: str, user_id: str):
        try:
            if user_id == AdminUser or user_id == await cls._get_user_by_tool_id(user_id):
                await ToolDao.delete_tool_by_id(tool_id=tool_id)
            else:
                raise ValueError('No Permission Exec')
        except Exception as err:
            raise ValueError(f'Delete Tool Appear Error: {err}')

    @classmethod
    async def update_tool(cls, tool_id: str, user_id: str, zh_name: str,
                          en_name: str, description: str, logo_url: str):
        try:
            if user_id == AdminUser or user_id == await cls._get_user_by_tool_id(user_id):
                await ToolDao.update_tool_by_id(tool_id=tool_id, zh_name=zh_name, logo_url=logo_url,
                                                en_name=en_name, description=description)
            else:
                raise ValueError('No Permission Exec')
        except Exception as err:
            raise ValueError(f'Update Tool Appear Error: {err}')

    @classmethod
    async def get_personal_tool_by_user(cls, user_id: str):
        try:
            personal_results = await ToolDao.get_tool_by_user_id(user_id=user_id)
            return [res[0].to_dict() for res in personal_results]
        except Exception as err:
            raise ValueError(f'Get Tool By User Id Appear Error: {err}')

    @classmethod
    async def get_visible_tool_by_user(cls, user_id: str):
        try:
            personal_results = await ToolDao.get_tool_by_user_id(user_id=user_id)
            system_results = await ToolDao.get_tool_by_user_id(user_id=AdminUser)
            return [res[0].to_dict() for res in personal_results + system_results]
        except Exception as err:
            raise ValueError(f'Get All Tool By User Appear Error: {err}')

    @classmethod
    async def get_all_tools(cls):
        try:
            tools = await ToolDao.get_all_tools()
            return [tool.to_dict() for tool in tools]
        except Exception as err:
            raise ValueError(f'Get All Tools Appear Error: {err}')

    @classmethod
    async def get_tool_name_by_id(cls, tool_id: Union[List[str], str]):
        try:
            if isinstance(tool_id, str):
                tools = await ToolDao.get_tool_name_by_id(tool_id=[tool_id])
            else:
                tools = await ToolDao.get_tool_name_by_id(tool_id=tool_id)
            result = []
            for tool in tools:
                result.append(tool[0].en_name)
            return result
        except Exception as err:
            raise ValueError(f'Get Tool name by Id appear Err: {err}')

    @classmethod
    async def _get_user_by_tool_id(cls, tool_id: str):
        try:
            tool = await ToolDao.get_tool_by_id(tool_id=tool_id)
            return tool[0].tool_id
        except Exception as err:
            raise ValueError(f'Get user by tool Id appear Error: {err}')

    @classmethod
    async def get_tools_data(cls):
        try:
            tools = await ToolDao.get_all_tools()
            return [tool[0].to_dict() for tool in tools]
        except Exception as err:
            raise ValueError(f'Get tools data appear Error: {err}')

    @classmethod
    async def get_id_by_tool_name(cls, tool_name: str, user_id: str):
        try:
            tool = await ToolDao.get_id_by_tool_name(tool_name, user_id)
            return tool[0].tool_id
        except Exception as err:
            raise ValueError(f'Get Id by tool name appear Error: {err}')
