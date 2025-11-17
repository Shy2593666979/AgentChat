from typing import Optional
from loguru import logger
from fastapi import APIRouter, Depends, Body

from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.schema.mcp_user_config import MCPUserConfigCreateRequest, MCPUserConfigUpdateRequest

router = APIRouter(tags=["MCP-User-Config"])

@router.post('/mcp_user_config/create', response_model=UnifiedResponseModel)
async def create_mcp_user_config(*,
                               config_request: MCPUserConfigCreateRequest,
                               login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await MCPUserConfigService.create_mcp_user_config(
            mcp_server_id=config_request.mcp_server_id,
            user_id=login_user.user_id,
            config=config_request.config
        )
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))

@router.get('/mcp_user_config/{config_id}', response_model=UnifiedResponseModel)
async def get_mcp_user_config_by_id(config_id: str,
                                   login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await MCPUserConfigService.get_mcp_user_config_from_id(config_id=config_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))

@router.put('/mcp_user_config/update', response_model=UnifiedResponseModel)
async def update_mcp_user_config(*,
                                config_request: MCPUserConfigUpdateRequest,
                                login_user: UserPayload = Depends(get_login_user)):
    try:
        await MCPUserConfigService.update_mcp_user_config(
            mcp_server_id=config_request.server_id,
            user_id=login_user.user_id,
            config=config_request.config
        )
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))

@router.delete('/mcp_user_config/delete', response_model=UnifiedResponseModel)
async def delete_mcp_user_config(config_id: str = Body(embed=True, description='配置ID'),
                                login_user: UserPayload = Depends(get_login_user)):
    try:
        await MCPUserConfigService.delete_mcp_user_config(config_id=config_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))

@router.get('/mcp_user_config', response_model=UnifiedResponseModel)
async def get_mcp_user_config(*,
                             server_id: str,
                             login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await MCPUserConfigService.show_mcp_user_config(
            user_id=login_user.user_id,
            mcp_server_id=server_id
        )
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
