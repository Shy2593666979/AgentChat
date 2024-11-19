from database.models.user import AdminUser
from database.dao.tool import ToolDao
from typing import List, Union
from type.schemas import resp_200, resp_500
from loguru import logger


class ToolService:

    @classmethod
    def create_tool(cls, user_id: str, zh_name: str, en_name: str, description: str):
        try:
            ToolDao.create_tool(user_id=user_id, zh_name=zh_name,
                                en_name=en_name, description=description)
            return resp_200()
        except Exception as err:
            logger.error(f'create tool appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def delete_tool(cls, tool_id: str, user_id: str):
        try:
            if user_id == AdminUser or user_id == cls._get_user_by_tool_id(user_id):
                ToolDao.delete_tool_by_id(tool_id=tool_id)
                return resp_200()
            else:
                return resp_500(message='no permission exec')
        except Exception as err:
            logger.error(f'delete tool appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def update_tool(cls, tool_id: str, user_id: str,zh_name: str=None,
                    en_name: str=None, description: str=None):
        try:
            if user_id == AdminUser or user_id == cls._get_user_by_tool_id(user_id):
                ToolDao.update_tool_by_id(tool_id=tool_id, zh_name=zh_name,
                                          en_name=en_name, description=description)
                return resp_200()
            else:
                return resp_500(message='no permission exec')
        except Exception as err:
            logger.error(f'update tool appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def get_personal_tool_by_user(cls, user_id: str):
        try:
            personal_data = ToolDao.get_tool_by_user_id(user_id=user_id)
            result = []
            for data in personal_data:
                result.append(data[0])
            return resp_200(data=result)
        except Exception as err:
            logger.error(f'get tool by user id appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def get_visible_tool_by_user(cls, user_id: str):
        try:
            personal_data = ToolDao.get_tool_by_user_id(user_id=user_id)
            system_data = ToolDao.get_tool_by_user_id(user_id=AdminUser)
            result = []
            for data in set(personal_data + system_data):
                result.append(data[0])
            return resp_200(data=result)
        except Exception as err:
            logger.error(f'get all tool by user appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def get_all_tools(cls):
        try:
            result = []
            tools_data = ToolDao.get_all_tools()
            for data in tools_data:
                result.append(data[0])
            return resp_200(data=result)
        except Exception as err:
            logger.error(f'get all tools appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def get_tool_name_by_id(cls, tool_id: Union[List[str], str]):
        try:
            if isinstance(tool_id, str):
                tools = ToolDao.get_tool_name_by_id(tool_id=[tool_id])
            else:
                tools = ToolDao.get_tool_name_by_id(tool_id=tool_id)
            result = []
            for tool in tools:
                result.append(tool[0].en_name)
            return result
        except Exception as err:
            logger.error(f'get tool name by id appear Err: {err}')
            return resp_500(message=str(err))

    @classmethod
    def _get_user_by_tool_id(cls, tool_id: str):
        try:
            tool = ToolDao.get_tool_by_id(tool_id=tool_id)
            return tool.tool_id
        except Exception as err:
            logger.error(f'get user by tool id appear Err: {err}')
            raise ValueError(str(err))
