from loguru import logger
from fastapi import APIRouter, Depends, Body, HTTPException

from agentchat.database import ToolTable
from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.api.services.tool import ToolService
from agentchat.schema.tool import ToolCreateReq, ToolUpdateReq, ToolDeleteReq
from agentchat.settings import app_settings
from agentchat.tools.openapi_tool.adapter import OpenAPIToolAdapter

router = APIRouter(tags=["Tool"], prefix="/tool")

@router.post("/create", response_model=UnifiedResponseModel)
async def create_tool(
    *,
    req: ToolCreateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        if req.openapi_schema: # 验证上传的OpenAPI Schema是否有效
            OpenAPIToolAdapter.validate_openapi_schema(req.openapi_schema)

        result = await ToolService.create_user_defined_tool(
            ToolTable(
                **req.model_dump(),
                user_id=login_user.user_id,
                is_user_defined=True,
            )
        )
        return resp_200(data=result)
    except Exception as err:
        logger.error(f"创建工具失败：{err}")
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/all", summary="获取当前用户可见的所有工具")
async def get_all_tools(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await ToolService.get_all_tools(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        logger.error(f"获取用户可见工具失败：{err}")
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/user_defined", summary="获得用户自定义的工具")
async def get_user_defined_tools(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await ToolService.get_user_defined_tools(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        logger.error(f"获取用户自定义工具失败：{err}")
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/delete", response_model=UnifiedResponseModel)
async def delete_user_defined_tool(
    req: ToolDeleteReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证用户权限
        await ToolService.verify_user_permission(req.tool_id, login_user.user_id)

        await ToolService.delete_user_defined_tool(tool_id=req.tool_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post("/update", summary="修改用户自定义的工具")
async def update_user_defined_tool(
    req: ToolUpdateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        if req.openapi_schema:
            OpenAPIToolAdapter.validate_openapi_schema(req.openapi_schema)

        # 验证用户权限
        await ToolService.verify_user_permission(req.tool_id, login_user.user_id)

        await ToolService.update_user_defined_tool(
            tool_id=req.tool_id,
            update_values=req.model_dump(exclude_none=True, exclude={"tool_id"})
        )
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/default_logo", summary="获得工具默认的头像")
async def get_default_tol_logo(
    login_user: UserPayload = Depends(get_login_user)
):
    return resp_200(data={"logo_url": app_settings.default_config.get("tool_logo_url")})