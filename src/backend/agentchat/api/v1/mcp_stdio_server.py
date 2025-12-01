from fastapi import APIRouter, Body, Depends
from loguru import logger

from agentchat.api.services.mcp_stdio_server import MCPServerService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schema.schemas import resp_200, resp_500

router = APIRouter(tags=["MCP-Stdio-Server"])


@router.post("/mcp_stdio_server")
async def create_mcp_server(
        name: str = Body(),
        mcp_server_env: str = Body(None),
        mcp_server_path: str = Body(),
        mcp_server_command: str = Body(),
        login_user: UserPayload = Depends(get_login_user)):
    try:
        MCPServerService.create_mcp_server(name, mcp_server_path,
                                           login_user.user_id, mcp_server_command, mcp_server_env)
        return resp_200()
    except Exception as err:
        logger.error(f"Create MCP Server Error: {err}")
        return resp_500(data=str(err))


@router.get("/mcp_stdio_server")
async def get_mcp_servers(login_user: UserPayload = Depends(get_login_user)):
    try:
        mcp_servers = MCPServerService.get_mcp_servers(login_user.user_id)
        results = []
        for server in mcp_servers:
            results.append({
                "user_id": server.user_id,
                "name": server.name,
                "mcp_server_env": server.mcp_server_env,
                "mcp_server_id": server.mcp_server_id,
                "mcp_server_path": server.mcp_server_path,
                "mcp_server_command": server.mcp_server_command,
                "create_time": server.create_time
            })
        return resp_200(data=results)
    except Exception as err:
        logger.error(f"Get MCP Server Error: {err}")
        return resp_500(data=str(err))


@router.delete("/mcp_stdio_server")
async def delete_mcp_server(mcp_server_id: str = Body(embed=True),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        MCPServerService.delete_mcp_server(login_user.user_id, mcp_server_id)
        return resp_200()
    except Exception as err:
        logger.error(f"Delete MCP Server Error: {err}")
        return resp_500(data=str(err))


@router.put("/mcp_stdio_server")
async def update_mcp_server(
        mcp_server_id: str = Body(...),
        name: str = Body(None),
        mcp_server_command: str = Body(None),
        mcp_server_path: str = Body(None),
        mcp_server_env: str = Body(None),
        login_user: UserPayload = Depends(get_login_user)):
    try:
        MCPServerService.update_mcp_server(mcp_server_id, mcp_server_path, name,
                                           login_user.user_id, mcp_server_command, mcp_server_env)
        return resp_200()
    except Exception as err:
        logger.error(f"Update MCP Server Error: {err}")
        return resp_500(data=str(err))
