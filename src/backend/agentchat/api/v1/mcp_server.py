import json
from typing import Optional

from fastapi import APIRouter, Body, Depends

from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.mcp import McpAsToolPrompt
from agentchat.schema.mcp import MCPResponseFormat
from agentchat.schema.schemas import resp_500, resp_200
from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.services.mcp.manager import MCPManager
from loguru import logger

from agentchat.utils.convert import convert_mcp_config

router = APIRouter(tags=["MCP-Server"])


@router.post("/mcp_server")
async def create_mcp_server(server_name: str = Body(..., description="MCP Server的名称"),
                            url: str = Body(..., description="MCP Server 的URL"),
                            type: str = Body(..., description="MCP Server 的连接方式，SSE、Websocket"),
                            config: dict = Body(None, description="MCP Server 的配置信息"),
                            logo_url: Optional[str] = Body("xxxx", description="MCP Server 的LOGO"),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        server_info = {
            "server_name": server_name,
            "type": type,
            "url": url
        }
        mcp_manager = MCPManager(
            [convert_mcp_config(server_info)]
        )
        tools_params = await mcp_manager.show_mcp_tools()
        tools_name_str = []
        for key, tools in tools_params.items():
            for tool in tools:
                tools_name_str.append(tool["name"])
        config_enabled = True if config else False

        structured_agent = StructuredResponseAgent(MCPResponseFormat)
        structured_response = structured_agent.get_structured_response(
            McpAsToolPrompt.format(tools_info=json.dumps(tools_params, indent=4)))

        await MCPService.create_mcp_server(server_name, login_user.user_id, login_user.user_name, url, type, config,
                                           tools_name_str, tools_params.get(server_name), config_enabled, logo_url,
                                           structured_response.mcp_as_tool_name, structured_response.description)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/mcp_server")
async def get_mcp_servers(login_user: UserPayload = Depends(get_login_user)):
    try:
        mcp_servers = await MCPService.get_all_servers(login_user.user_id)
        return resp_200(data=mcp_servers)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/mcp_server")
async def delete_mcp_server(server_id: str = Body(..., description="MCP Server 的ID", embed=True),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)

        await MCPService.delete_server_from_id(server_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/mcp_tools")
async def get_mcp_tools(server_id: str = Body(..., description="MCP Server 的ID", embed=True),
                        login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)

        results = await MCPService.get_mcp_tools_info(server_id)
        return resp_200(results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/mcp_server")
async def update_mcp_server(server_id: str = Body(..., description="MCP Server 的ID"),
                            server_name: str = Body(None, description="MCP Server的名称"),
                            url: str = Body(None, description="MCP Server 的URL"),
                            type: str = Body(None, description="MCP Server 的连接方式，SSE、Websocket"),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)
        mcp_server = await MCPService.get_mcp_server_from_id(server_id)

        if url != mcp_server["url"]:
            server_info = {
                "server_name": server_name,
                "type": type,
                "url": url
            }
            mcp_manager = MCPManager([convert_mcp_config(server_info)])
            tools_params = await mcp_manager.show_mcp_tools()
            tools_str = []
            for key, tools in tools_params:
                for tool in tools:
                    tools_str.append(tool["name"])

            structured_agent = StructuredResponseAgent(MCPResponseFormat)
            structured_response = structured_agent.get_structured_response(
                McpAsToolPrompt.format(tools_info=json.dumps(tools_params, indent=4)))

            await MCPService.update_mcp_server(server_id, server_name, url, type,
                                               mcp_as_tool_name=structured_response.mcp_as_tool_name,
                                               description=structured_response.description, tools=tools_str,
                                               params=tools_params.get(server_name))
        else:
            await MCPService.update_mcp_server(server_id, server_name)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500()
