"""
MCP 注册与工具聚合的业务逻辑层
"""

import json
import re
import uuid
from loguru import logger
from typing import Any
from cachetools import TTLCache

from agentchat.schemas.register_mcp import RegisterMcpRequest, RegisterMcpResponse, RegisterMcpServerModel
from agentchat.mcp_proxy.schema_converter import tool_to_mcp_schema, _parse_openapi_schema
from agentchat.mcp_proxy.execute_tool import RegisterMcpToolExecute
from agentchat.database.dao.register_mcp import RegisterMcpDao
from agentchat.database.models.register_mcp import RegisterMcpServer
from agentchat.database.models.register_mcp_tool import RegisterMcpTool
from agentchat.settings import app_settings

_tool_cache: TTLCache = TTLCache(maxsize=200, ttl=300)

def _slugify(text: str) -> str:
    """将任意字符串转为合法标识符（字母/数字/下划线，不以数字开头）"""
    slug = re.sub(r"[^A-Za-z0-9_]", "_", text).strip("_")
    if slug and slug[0].isdigit():
        slug = "_" + slug
    return slug or "mcp_service"


def _parse_openapi_tools(schema: dict, base_url: str) -> list[RegisterMcpTool]:
    """从 OpenAPI 3.1+ 文档解析出 Tool 列表（mcp_id 留空，由调用方填充）"""
    tools: list[RegisterMcpTool] = []
    paths: dict[str, Any] = schema.get("paths", {})
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in http_methods:
                continue
            if not isinstance(operation, dict):
                continue

            op_id: str = operation.get("operationId") or f"{method}_{path}"
            tool_name = _slugify(op_id)
            description: str = operation.get("summary") or operation.get("description") or tool_name

            # 构造 parameters schemas（复用现有 _parse_openapi_schema 格式）
            parameters_payload: dict = {
                "parameters": operation.get("parameters", []),
            }
            if "requestBody" in operation:
                parameters_payload["requestBody"] = operation["requestBody"]
            parsed_parameters = _parse_openapi_schema(parameters_payload)

            api_info = {
                "base_url": base_url,
                "path": path,
                "method": method.upper(),
                "content_type": "application/json",
            }

            tools.append(RegisterMcpTool(
                register_mcp_id="",  # 调用方填充
                name=tool_name,
                description=description,
                parameters=json.dumps(parsed_parameters),
                api_info=api_info,
            ))

    return tools

class RegisterMcpService:

    @classmethod
    async def register_mcp(cls, body: RegisterMcpRequest, user_id: str) -> RegisterMcpResponse:
        schema = body.openapi_schema
        info_block: dict = schema.get("info", {})

        # 推断 base_url：取 servers[0].url，fallback 空字符串
        servers: list = schema.get("servers", [])
        base_url: str = servers[0].get("url", "") if servers else ""

        # 推断 name
        name = body.name or info_block.get("title", "")
        # name = _slugify(raw_name) if raw_name else "mcp_service"

        # 推断 description
        description = body.description or info_block.get("description")

        mcp_id = body.mcp_id or str(uuid.uuid4())

        tools = _parse_openapi_tools(schema, base_url)
        for t in tools:
            t.register_mcp_id = mcp_id


        remote_url = cls._generate_remote_url(mcp_id, body.transport)
        existing = await RegisterMcpDao.get_by_id(mcp_id)
        if not existing:
            mcp = RegisterMcpServer(
                id=mcp_id,
                name=name,
                user_id=user_id,
                remote_url=remote_url,
                transport=body.transport,
                description=description,
            )
            await RegisterMcpDao.save_mcp_with_tools(mcp, tools)
        else:
            mcp = existing
            for t in tools:
                await RegisterMcpDao.save_tool(t)

        _tool_cache.pop(mcp_id, None)


        return RegisterMcpResponse(mcp_id=mcp_id, remote_url=remote_url, name=name, tool_count=len(tools))


    @classmethod
    async def register_mcp_by_completion(cls, server: RegisterMcpServerModel, mcp_id: str=None, user_id: str=None):
        register_mcp_id = mcp_id or str(uuid.uuid4())
        remote_url = cls._generate_remote_url(register_mcp_id, server.transport)
        mcp_tools = []
        mcp_server = RegisterMcpServer(
            id=register_mcp_id,
            name=server.name,
            user_id=user_id,
            remote_url=remote_url,
            description=server.description,
            transport=server.transport
        )

        for tool in server.tools:
            mcp_tools.append(
                RegisterMcpTool(
                    name=tool.name,
                    register_mcp_id=register_mcp_id,
                    description=tool.description,
                    parameters=json.dumps(tool.parameters.model_dump()),
                    api_info=tool.api_info.model_dump()
                )
            )

        await RegisterMcpDao.save_mcp_with_tools(mcp_server, mcp_tools)
        return RegisterMcpResponse(mcp_id=register_mcp_id, remote_url=remote_url, name=server.name, tool_count=len(mcp_tools))


    @classmethod
    async def get_tools_for_server(cls, server_key: str) -> list[dict]:
        if server_key in _tool_cache:
            return _tool_cache[server_key]
        tools = await RegisterMcpDao.get_tools_by_mcp_id(server_key)
        schemas = [tool_to_mcp_schema(t) for t in tools]
        _tool_cache[server_key] = schemas
        logger.info(f"Aggregated {len(schemas)} tools for server: {server_key}")
        return schemas

    @classmethod
    async def call_tool(cls, server_key: str, tool_name: str, arguments: dict) -> dict:
        tool = await RegisterMcpDao.get_tool_by_name(server_key, tool_name)
        if tool is None:
            logger.warning(f"Tool not found: {tool_name} in server: {server_key}")
            return {"isError": True, "content": [{"type": "text", "text": f"Tool not found: {tool_name}"}]}
        return await RegisterMcpToolExecute.execute_http_tool(tool, arguments)


    @classmethod
    def _generate_remote_url(cls, mcp_id, transport):
        suffix = "/sse" if transport.lower() == "sse" else ""
        prefix_url = "https://" if app_settings.server.env == "prod" else "http://"
        remote_url = f"{prefix_url}{app_settings.server.host}/mcp/{mcp_id}{suffix}"

        return remote_url