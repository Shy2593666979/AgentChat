from agentchat.database.dao.mcp_server import MCPServerDao
from agentchat.database.models.user import AdminUser, SystemUser


class MCPService:

    @classmethod
    def create_mcp_server(cls, mcp_server_name: str, user_id: str, user_name: str,
                          url: str, type: str, config: dict, tools: str, params: dict, config_enabled: bool):
        try:
            return MCPServerDao.create_mcp_server(mcp_server_name, user_id, user_name, url, type,
                                                  config, tools, params, config_enabled)
        except Exception as err:
            raise ValueError(f"Create MCP Server Error: {err}")

    @classmethod
    def get_mcp_server_from_id(cls, mcp_server_id):
        try:
            return MCPServerDao.get_mcp_server_from_id(mcp_server_id)
        except Exception as err:
            raise ValueError(f"Get MCP Server From ID Error: {err}")

    @classmethod
    def update_mcp_server(cls, mcp_server_id: str, mcp_server_name: str,
                          url: str, type: str, config: dict, tools: str, params: dict):
        try:
            return MCPServerDao.update_mcp_server(mcp_server_id, mcp_server_name, url, type, config,
                                                  tools, params)
        except Exception as err:
            raise ValueError(f"Update MCP Server Error: {err}")

    @classmethod
    def get_server_from_tool_name(cls, tool_name):
        try:
            results = MCPServerDao.get_server_from_tool_name(tool_name)
            return [res[0].to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get Server From Tool Name Error: {err}")

    @classmethod
    def delete_server_from_id(cls, mcp_server_id):
        try:
            return MCPServerDao.delete_mcp_server(mcp_server_id)
        except Exception as err:
            raise ValueError(f"Delete Server From ID Error: {err}")

    @classmethod
    def get_all_servers(cls, user_id):
        try:
            personal_servers = MCPServerDao.get_mcp_servers(user_id)
            admin_servers = MCPServerDao.get_mcp_servers(SystemUser)
            all_servers = personal_servers + admin_servers
            return [server[0].to_dict() for server in all_servers]
        except Exception as err:
            raise ValueError(f"Get All Servers Error: {err}")