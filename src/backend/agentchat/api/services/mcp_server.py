from agentchat.database.dao.mcp_server import MCPServerDao
from agentchat.database.models.user import AdminUser, SystemUser


class MCPService:

    @classmethod
    async def create_mcp_server(cls, server_name: str, user_id: str, user_name: str,
                                url: str, type: str, config: dict, tools: list, params: dict,
                                config_enabled: bool = False):
        try:
            return await MCPServerDao.create_mcp_server(server_name, user_id, user_name, url, type,
                                                        config, tools, params, config_enabled)
        except Exception as err:
            raise ValueError(f"Create MCP Server Error: {err}")

    @classmethod
    async def get_mcp_server_from_id(cls, mcp_server_id):
        try:
            return await MCPServerDao.get_mcp_server_from_id(mcp_server_id)
        except Exception as err:
            raise ValueError(f"Get MCP Server From ID Error: {err}")

    @classmethod
    async def update_mcp_server(cls, mcp_server_id: str, server_name: str = None, url: str = None, type: str = None,
                                config: dict = None, tools: list = None, params: dict = None):
        try:
            return await MCPServerDao.update_mcp_server(mcp_server_id, server_name, url, type, config,
                                                        tools, params)
        except Exception as err:
            raise ValueError(f"Update MCP Server Error: {err}")

    @classmethod
    async def get_server_from_tool_name(cls, tool_name):
        try:
            results = await MCPServerDao.get_server_from_tool_name(tool_name)
            return results[0].to_dict()
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
            if user_id not in (mcp_server[0].user_id, AdminUser):
                raise ValueError(f"没有权限访问")
        else:
            raise ValueError(f"服务不存在")

    @classmethod
    async def get_all_servers(cls, user_id):
        try:
            # 管理员可看见所有用户的MCP Server
            if user_id in (AdminUser, SystemUser):
                all_servers = await MCPServerDao.get_all_mcp_servers()
                return [server[0].to_dict() for server in all_servers]
            else:
                personal_servers = await MCPServerDao.get_mcp_servers_from_user(user_id)
                admin_servers = await MCPServerDao.get_mcp_servers_from_user(SystemUser)
                all_servers = personal_servers + admin_servers
                return [server[0].to_dict() for server in all_servers]
        except Exception as err:
            raise ValueError(f"Get All Servers Error: {err}")

    @classmethod
    async def get_mcp_tools_info(cls, server_id):
        try:
            servers = await MCPServerDao.get_mcp_server_from_id(server_id)
            server = servers[0].to_dict()
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
