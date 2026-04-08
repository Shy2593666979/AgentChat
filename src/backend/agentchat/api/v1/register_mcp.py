from loguru import logger
from fastapi import APIRouter, Depends
from pydantic import ValidationError

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.database.dao.register_mcp import RegisterMcpDao
from agentchat.schemas.register_mcp import RegisterMcpRequest
from agentchat.schemas.openapi import OpenApiSchema
from agentchat.api.responses.builder import resp_200
from agentchat.mcp_proxy.register_mcp import RegisterMcpService

router = APIRouter(prefix="/mcp", tags=["Register-MCP"])

@router.post("/register", summary="根据传来的OpenAPI格式数据生成")
async def register_mcp_server(
    req: RegisterMcpRequest,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        OpenApiSchema.model_validate(req.openapi_schema)
    except ValidationError as err:
        logger.error(f"传入不合法的OpenAPI Schema: {err}")
        raise err
    result = await RegisterMcpService.register_mcp(req, login_user.user_id)
    return resp_200(data=result)


@router.get("/list", summary="获取注册的MCP列表")
async def get_all_register_mcps(
    login_user: UserPayload = Depends(get_login_user)
):
    results = await RegisterMcpDao.get_all(login_user.user_id)

    results = sorted([
        {
            **mcp.model_dump(),
            "mcp_tools": [tool.model_dump() for tool in mcp.mcp_tools]
        }
        for mcp in results
    ], key=lambda x: x["updated_time"], reverse=True)

    return resp_200(data=results)
