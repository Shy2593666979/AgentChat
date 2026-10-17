from fastapi import APIRouter, Body, Depends
from loguru import logger

from agentchat.api.responses.builder import resp_200, resp_500
from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schemas.mcp import MCPServerImportedReq, MCPServerUpdateReq
from agentchat.services.mcp.metadata import queue_metadata
from agentchat.settings import app_settings

router = APIRouter(tags=["MCP-Server"])


@router.post("/mcp_server")
async def create_mcp_server(
    req: MCPServerImportedReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        MCPService.validate_imported_config(req.imported_config)
        name, info = next(iter(req.imported_config.get("mcpServers", {}).items()))
        server_info = {
            "server_name": req.server_name or name,  # 传入Mcp Server名称优先级更高
            "type": info.get("type", "sse"),
            "headers": info.get("headers"),
            "url": info.get("url"),
        }
        server_id = await MCPService.create_user_mcp_server(
            server_info, login_user.user_id, login_user.user_name,
            logo_url=req.logo_url, imported_config=req.imported_config)
        return resp_200(
            data={
                "mcp_server_id": server_id,
                "metadata_status": "pending",
            },
            message="服务已保存，工具信息与描述将在后台生成",
        )
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
async def delete_mcp_server(
    server_id: str = Body(..., description="MCP Server 的ID", embed=True),
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)

        await MCPService.delete_server_from_id(server_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/mcp_tools")
async def get_mcp_tools(
    server_id: str = Body(..., description="MCP Server 的ID", embed=True),
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)

        results = await MCPService.get_mcp_tools_info(server_id)
        return resp_200(results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/mcp_server")
async def update_mcp_server(
    req: MCPServerUpdateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(req.server_id, login_user.user_id)
        mcp_server = await MCPService.get_mcp_server_from_id(req.server_id)

        update_data = {}
        if req.name is not None:
            update_data["server_name"] = req.name
        if req.logo_url is not None:
            update_data["logo_url"] = req.logo_url
        if req.imported_config and req.imported_config != mcp_server["imported_config"]:
            MCPService.validate_imported_config(req.imported_config)
            name, info = next(iter(req.imported_config["mcpServers"].items()))
            update_data.update(
                {
                    "server_name": req.name or name,
                    "url": info["url"],
                    "type": info["type"],
                    "imported_config": req.imported_config,
                    "tools": [],
                    "params": [],
                }
            )
            if mcp_server["user_id"] == "0":
                await MCPService.update_mcp_server(req.server_id, update_data)
                return resp_200()
            queue_metadata(req.server_id, update_data)
            return resp_200(
                data={
                    "metadata_status": "pending",
                },
                message="服务已保存，正在后台更新工具信息与描述",
            )
        await MCPService.update_mcp_server(req.server_id, update_data)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500()

@router.post("/mcp_server/{server_id}/metadata/retry")
async def retry_mcp_metadata(server_id: str, login_user: UserPayload = Depends(get_login_user)):
    try:
        await MCPService.verify_user_permission(server_id, login_user.user_id)
        server = await MCPService.get_mcp_server_from_id(server_id)
        if server["user_id"] == "0":
            raise ValueError("默认服务使用固定描述，无需生成")
        queue_metadata(server_id)
        return resp_200(
            data={
                "metadata_status": "pending",
            }
        )
    except Exception as err:
        return resp_500(message=str(err))


@router.get("/mcp_server/logo", summary="获得MCP服务的默认头像")
async def get_mcp_default_logo(
    login_user: UserPayload = Depends(get_login_user)
):
    return resp_200(
        {
            "logo_url": app_settings.default_config.get("mcp_logo_url"),
        }
    )
