from typing import Optional
from loguru import logger
from fastapi import APIRouter, Depends, Body

from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.api.services.tool import ToolService
from agentchat.schema.tool import ToolCreateRequest, ToolUpdateRequest

router = APIRouter(tags=["Tool"])


@router.post('/tool/create', response_model=UnifiedResponseModel)
async def create_tool(*,
                      tool_request: ToolCreateRequest,
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await ToolService.create_tool(user_id=login_user.user_id, zh_name=tool_request.zh_name,
                                                en_name=tool_request.en_name, description=tool_request.description,
                                                logo_url=tool_request.logo_url)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get('/tool/all', response_model=UnifiedResponseModel)
async def get_tool(login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await ToolService.get_all_tools()
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post('/tool/own', response_model=UnifiedResponseModel)
async def get_personal_tool(login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await ToolService.get_personal_tool_by_user(user_id=login_user.user_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post('/tool/visible', response_model=UnifiedResponseModel)
async def get_visible_tool(login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await ToolService.get_visible_tool_by_user(user_id=login_user.user_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete('/tool/delete', response_model=UnifiedResponseModel)
async def delete_tool(tool_id: str = Body(embed=True, description='工具的ID'),
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await ToolService.verify_user_permission(tool_id, login_user.user_id)

        await ToolService.delete_tool(tool_id=tool_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put('/tool/update', response_model=UnifiedResponseModel)
async def update_tool(*,
                      tool_request: ToolUpdateRequest,
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await ToolService.verify_user_permission(tool_request.tool_id, login_user.user_id)

        await ToolService.update_tool(tool_id=tool_request.tool_id, logo_url=tool_request.logo_url,
                                      en_name=tool_request.en_name, zh_name=tool_request.zh_name,
                                      description=tool_request.description)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
