from typing import Any, Dict
from uuid import uuid4

from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.api.services.user import UserService
from agentchat.database.dao.mcp_server import MCPServerDao
from agentchat.database.models.user import AdminUser, SystemUser
from agentchat.services.mcp.metadata import (
    forget_metadata,
    metadata_statuses,
    queue_metadata,
)
from agentchat.settings import app_settings


class MCPService:

    @classmethod
    async def create_mcp_server(
        cls,
        url: str,
        type: str,
        tools: list,
        params: dict,
        server_name: str,
        user_id: str,
        user_name: str,
        logo_url: str,
        mcp_as_tool_name: str,
        description: str,
        config: dict = None,
        imported_config: dict = None,
        config_enabled: bool = False,
    ):
        return await MCPServerDao.create_mcp_server(
            url=url,
            type=type,
            config=config,
            tools=tools,
            params=params,
            server_name=server_name,
            user_id=user_id,
            user_name=user_name,
            mcp_as_tool_name=mcp_as_tool_name,
            description=description,
            config_enabled=config_enabled,
            logo_url=logo_url,
            imported_config=imported_config
        )

    @classmethod
    async def get_mcp_server_from_id(cls, mcp_server_id):
        result = await MCPServerDao.get_mcp_server_from_id(mcp_server_id)
        return result.to_dict()


    @classmethod
    async def update_mcp_server(cls, server_id: str, update_data: dict):
        if not update_data:
            return

        return await MCPServerDao.update_mcp_server(
            mcp_server_id=server_id,
            update_data=update_data
        )

    @classmethod
    async def get_server_from_tool_name(cls, tool_name):
        results = await MCPServerDao.get_server_from_tool_name(tool_name)
        return results.to_dict()

    @classmethod
    async def delete_server_from_id(cls, mcp_server_id):
        result = await MCPServerDao.delete_mcp_server(mcp_server_id)
        forget_metadata(mcp_server_id)
        return result

    @classmethod
    async def verify_user_permission(cls, server_id, user_id, action: str="update"):
        mcp_server = await MCPServerDao.get_mcp_server_from_id(server_id)
        if mcp_server:
            if user_id != mcp_server.user_id:
                raise ValueError(f"没有权限访问")
        else:
            raise ValueError(f"服务不存在")

    @classmethod
    async def get_all_servers(cls, user_id):
        # 管理页面仅显示当前用户的独立服务副本。
        all_servers = await MCPServerDao.get_mcp_servers_from_user(user_id)
        all_servers = [server.to_dict() for server in all_servers]
        statuses = metadata_statuses()
        for server in all_servers:
            # 进程内的异步任务不会在后端重启后自动恢复。
            unfinished = server.get("description") == "服务已保存，正在后台生成工具信息与描述。"
            server.update(
                statuses.get(
                    server["mcp_server_id"],
                    {
                        "metadata_status": "failed" if unfinished else "ready",
                        "metadata_error": "生成已中断，请重试。" if unfinished else "",
                    },
                )
            )
            user_config = await MCPUserConfigService.show_mcp_user_config(user_id, server["mcp_server_id"])
            if user_config.get("config"):
                server["config"] = user_config.get("config")
        return all_servers

    @classmethod
    async def get_mcp_tools_info(cls, server_id):
        server = await MCPServerDao.get_mcp_server_from_id(server_id)
        server = server.to_dict()
        tools_info = []
        for param in server["params"]:
            tool_schema = []
            properties = param["input_schema"]["properties"]
            required = param["input_schema"].get("required", [])
            for param_key, param_value in properties.items():
                tool_schema.append(
                    {
                        "name": param_key,
                        "description": param_value.get("description", ""),
                        "type": param_value.get("type"),
                        "required": True if param_key in required else False,
                    }
                )

            tools_info.append(
                {
                    "tool_name": param["name"],
                    "tool_description": param.get("description", ""),
                    "tool_schema": tool_schema,
                }
            )
        return tools_info

    @classmethod
    async def get_mcp_server_ids_from_name(cls, mcp_servers_name, user_id):
        mcp_servers = await MCPServerDao.get_mcp_server_ids_from_name(mcp_servers_name, user_id)
        return [mcp_server.mcp_server_id for mcp_server in mcp_servers]


    @classmethod
    def validate_imported_config(cls, payload: Dict[str, Any]):
        """
        校验前端传入的 mcpServers 配置

        规则：
        - 必须包含 mcpServers
        - mcpServers 必须是 dict
        - 每个 server 必须包含 type 和 url
        - headers 可选，但若存在必须是 dict
        """
        if "mcpServers" not in payload:
            raise ValueError("缺少字段: mcpServers")

        mcp_servers = payload["mcpServers"]

        if not isinstance(mcp_servers, dict):
            raise ValueError("mcpServers 必须是一个字典类型")

        if not mcp_servers:
            raise ValueError("mcpServers 不能为空")
        if len(mcp_servers) != 1:
            raise ValueError("一次只能添加一个 MCP 服务")

        for server_name, server_conf in mcp_servers.items():
            if not isinstance(server_name, str) or not server_name.strip():
                raise ValueError(f"非法的 mcpServer 名称: {server_name}")

            if not isinstance(server_conf, dict):
                raise ValueError(f"mcpServer `{server_name}` 配置必须是对象")
            if server_conf.get("type") not in {"sse", "streamable_http", "websocket"}:
                raise ValueError("不支持的 MCP 传输类型")

            # 必填字段
            for required_field in ("type", "url"):
                if required_field not in server_conf:
                    raise ValueError(f"mcpServer `{server_name}` 缺少必填字段: {required_field}")

                if not server_conf[required_field]:
                    raise ValueError(f"mcpServer `{server_name}` 字段 `{required_field}` 不能为空")

            # headers 可选
            if "headers" in server_conf and not isinstance(server_conf["headers"], dict):
                raise ValueError(f"mcpServer `{server_name}` 的 headers 必须是对象 (dict)")

    @classmethod
    async def create_user_mcp_server(cls, server_info, user_id, user_name, logo_url=None, imported_config=None):
        server_id = await cls.create_mcp_server(
            tools=[],
            params=[],
            url=server_info["url"],
            config={},
            type=server_info["type"],
            user_id=user_id,
            server_name=server_info["server_name"],
            user_name=user_name,
            config_enabled=False,
            logo_url=logo_url or app_settings.default_config.get("mcp_logo_url", ""),
            imported_config=imported_config
            or {
                "mcpServers": {
                    server_info["server_name"]: {
                        "url": server_info["url"],
                        "type": server_info["type"],
                        **(
                            {
                                "headers": server_info["headers"],
                            }
                            if server_info.get("headers")
                            else {}
                        ),
                    },
                },
            },
            description="服务已保存，正在后台生成工具信息与描述。",
            mcp_as_tool_name="mcp_service_" + uuid4().hex,
        )
        queue_metadata(server_id)
        return server_id

    @classmethod
    async def register_and_import_mcp_server(cls, server_info, user_id):
        user_name = UserService.get_user_info_by_id(user_id).get("user_name")
        return await cls.create_user_mcp_server(server_info, user_id, user_name)
