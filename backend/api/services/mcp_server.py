from database.dao.mcp_server import MCPServerDao
from database.models.user import AdminUser
from loguru import logger

class MCPServerService:

    @classmethod
    def create_mcp_server(cls, name: str, mcp_server_path: str,
                          user_id: str, mcp_server_command: str, mcp_server_env: str):
        return MCPServerDao.create_mcp_server(mcp_server_path, mcp_server_command, user_id, name, mcp_server_env)

    @classmethod
    def get_mcp_servers(cls, user_id):
        mcp_servers = MCPServerDao.get_mcp_servers(user_id)
        results = []
        for server in mcp_servers:
            results.append(server[0])
        return results

    @classmethod
    def delete_mcp_server(cls, user_id, mcp_server_id):
        mcp_server_user = cls.get_mcp_server_user(mcp_server_id)
        if user_id in (mcp_server_user, AdminUser):
            return MCPServerDao.delete_mcp_server(mcp_server_id)
        else:
            logger.error("No Permission Exec Delete MCP Server")
            raise ValueError("No Permission Exec Delete MCP Server")

    @classmethod
    def update_mcp_server(cls, mcp_server_id, mcp_server_path, name,
                          user_id, mcp_server_command, mcp_server_env):
        mcp_server_user = cls.get_mcp_server_user(mcp_server_id)
        if user_id in (mcp_server_user, AdminUser):
           return MCPServerDao.update_mcp_server(mcp_server_id, mcp_server_path, mcp_server_command, name, mcp_server_env)
        else:
            logger.error("No Permission Exec Update MCP Server")
            raise ValueError("No Permission Exec Update MCP Server")

    @classmethod
    def get_mcp_server_user(cls, mcp_server_id):
        mcp_server = MCPServerDao.get_mcp_server_by_id(mcp_server_id)
        return mcp_server.user_id