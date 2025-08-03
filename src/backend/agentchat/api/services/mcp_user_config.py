from typing import Optional, List
from agentchat.database.dao.mcp_user_config import MCPUserConfigDao
from agentchat.database.models.user import AdminUser, SystemUser


class MCPUserConfigService:
    @classmethod
    async def create_mcp_user_config(cls, mcp_server_id: str, user_id: str, config: Optional[List[dict]] = None):
        """
        创建一个新的MCP用户配置记录。
        :param mcp_server_id: MCP Server ID
        :param user_id: 用户ID
        :param config: 配置信息（可选）
        :return: 创建的MCP用户配置记录
        """
        try:
            return await MCPUserConfigDao.create_mcp_user_config(mcp_server_id, user_id, config)
        except Exception as err:
            raise ValueError(f"Create MCP User Config Error: {err}")

    @classmethod
    async def get_mcp_user_config_from_id(cls, config_id: str):
        """
        根据ID获取MCP用户配置记录。
        :param config_id: 配置记录ID
        :return: 查询结果
        """
        try:
            results = await MCPUserConfigDao.get_mcp_user_config_from_id(config_id)
            return results.to_dict()
        except Exception as err:
            raise ValueError(f"Get MCP User Config From ID Error: {err}")

    @classmethod
    async def update_mcp_user_config(cls,mcp_server_id: str, user_id: str, config: Optional[List[dict]] = None):
        """
        更新MCP用户配置记录。
        :param config_id: 配置记录ID
        :param mcp_server_id: MCP Server ID
        :param user_id: 用户ID
        :param config: 配置信息（可选）
        :return: None
        """
        try:
            user_config = await cls.show_mcp_user_config(user_id, mcp_server_id)
            if not user_config.get("config"):
                # 创建一条记录
                await cls.create_mcp_user_config(mcp_server_id, user_id, config)
            else:
                await MCPUserConfigDao.update_mcp_user_config(mcp_server_id, user_id, config)
        except Exception as err:
            raise ValueError(f"Update MCP User Config Error: {err}")

    @classmethod
    async def delete_mcp_user_config(cls, config_id: str):
        """
        删除指定ID的MCP用户配置记录。
        :param config_id: 配置记录ID
        :return: None
        """
        try:
            return await MCPUserConfigDao.delete_mcp_user_config(config_id)
        except Exception as err:
            raise ValueError(f"Delete MCP User Config Error: {err}")

    @classmethod
    async def get_mcp_user_config(cls, user_id: str, mcp_server_id: str):
        """
        获取MCP用户配置记录列表。
        :param user_id: 用户ID
        :param mcp_server_id: MCP Server ID
        :return: 查询结果
        """
        # 针对Agent对话时使用
        try:
            result = await MCPUserConfigDao.get_mcp_user_configs(user_id, mcp_server_id)
            mcp_config = {}
            # 确认用户配置信息
            if result:
                for res in result.config:
                    mcp_config[res["key"]] = res["value"]
            return mcp_config
        except Exception as err:
            raise ValueError(f"Get MCP User Configs Error: {err}")

    @classmethod
    async def show_mcp_user_config(cls, user_id: str, mcp_server_id: str):
        try:
            result = await MCPUserConfigDao.get_mcp_user_configs(user_id, mcp_server_id)
            if result:
                return result.to_dict()
            else:
                return {}
        except Exception as err:
            raise ValueError(f"Get MCP User Configs Error: {err}")