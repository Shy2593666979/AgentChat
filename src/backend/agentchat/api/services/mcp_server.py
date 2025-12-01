from datetime import datetime, timedelta

import pytz

from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.database.dao.mcp_server import MCPServerDao
from agentchat.database.models.user import AdminUser, SystemUser


class MCPService:

    @classmethod
    async def create_mcp_server(cls, server_name: str, user_id: str, user_name: str,
                                url: str, type: str, config: dict, tools: list, params: dict,
                                config_enabled: bool, logo_url: str, mcp_as_tool_name: str, description: str):
        try:
            return await MCPServerDao.create_mcp_server(server_name, user_id, user_name, mcp_as_tool_name, description,
                                                        url, type, config, tools, params, config_enabled, logo_url)
        except Exception as err:
            raise ValueError(f"Create MCP Server Error: {err}")

    @classmethod
    async def get_mcp_server_from_id(cls, mcp_server_id):
        try:
            result = await MCPServerDao.get_mcp_server_from_id(mcp_server_id)
            return result.to_dict()
        except Exception as err:
            raise ValueError(f"Get MCP Server From ID Error: {err}")

    @classmethod
    async def update_mcp_server(cls, mcp_server_id: str, server_name: str = None, url: str = None, type: str = None,
                                mcp_as_tool_name=None, description=None, config: dict = None, tools: list = None,
                                params: dict = None, logo_url: str = None):
        try:
            return await MCPServerDao.update_mcp_server(mcp_server_id, server_name, mcp_as_tool_name, description, url,
                                                        type, config, tools, params, logo_url)
        except Exception as err:
            raise ValueError(f"Update MCP Server Error: {err}")

    @classmethod
    async def get_server_from_tool_name(cls, tool_name):
        try:
            results = await MCPServerDao.get_server_from_tool_name(tool_name)
            return results.to_dict()
        except Exception as err:
            raise ValueError(f"Get Server From Tool Name Error: {err}")

    @classmethod
    async def delete_server_from_id(cls, mcp_server_id):
        try:
            return await MCPServerDao.delete_mcp_server(mcp_server_id)
        except Exception as err:
            raise ValueError(f"Delete Server From ID Error: {err}")

    @classmethod
    async def verify_user_permission(cls, server_id, user_id, action: str="update"):
        mcp_server = await MCPServerDao.get_mcp_server_from_id(server_id)
        if mcp_server:
            if user_id not in (mcp_server.user_id, AdminUser):
                raise ValueError(f"没有权限访问")
        else:
            raise ValueError(f"服务不存在")

    @classmethod
    async def get_all_servers(cls, user_id):
        try:
            # 管理员可看见所有用户的MCP Server
            if user_id in (AdminUser, SystemUser):
                all_servers = await MCPServerDao.get_all_mcp_servers()
            else:
                personal_servers = await MCPServerDao.get_mcp_servers_from_user(user_id)
                admin_servers = await MCPServerDao.get_mcp_servers_from_user(SystemUser)
                all_servers = personal_servers + admin_servers
            all_servers = [server.to_dict() for server in all_servers]
            for server in all_servers:
                user_config = await MCPUserConfigService.show_mcp_user_config(user_id, server["mcp_server_id"])
                if user_config.get("config"):
                    server["config"] = user_config.get("config")
            return all_servers
        except Exception as err:
            raise ValueError(f"Get All Servers Error: {err}")

    @classmethod
    async def mcp_server_need_update(cls):
        server = await MCPServerDao.get_first_mcp_server()

        # 获取当前时间（使用与数据库相同的时区）
        current_time = datetime.now(pytz.timezone('Asia/Shanghai'))
        # 计算时间差
        time_difference = current_time - server.update_time.replace(tzinfo=pytz.timezone('Asia/Shanghai'))

        # 判断是否超过7天
        return time_difference > timedelta(days=7)

    @classmethod
    async def get_mcp_tools_info(cls, server_id):
        try:
            server = await MCPServerDao.get_mcp_server_from_id(server_id)
            server = server.to_dict()
            tools_info = []
            for param in server["params"]:
                tool_schema = []
                properties = param["input_schema"]["properties"]
                required = param["input_schema"].get("required", [])
                for param_key, param_value in properties.items():
                    tool_schema.append({
                        "name": param_key,
                        "description": param_value.get("description", ""),
                        "type": param_value.get("type"),
                        "required": True if param_key in required else False
                    })

                tools_info.append({
                    "tool_name": param["name"],
                    "tool_description": param.get("description", ""),
                    "tool_schema": tool_schema
                })
            return tools_info
        except Exception as err:
            raise ValueError(f"Get MCP Tools Info Error:{err}")

    @classmethod
    async def get_mcp_server_ids_from_name(cls, mcp_servers_name, user_id):
        try:
            mcp_servers = await MCPServerDao.get_mcp_server_ids_from_name(mcp_servers_name, user_id)
            mcp_servers.extend(await MCPServerDao.get_mcp_server_ids_from_name(mcp_servers_name, SystemUser))
            return [mcp_server.mcp_server_id for mcp_server in mcp_servers]
        except Exception as err:
            raise ValueError(f"Get MCP Server Ids Error:{err}")

