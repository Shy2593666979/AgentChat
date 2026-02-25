from typing import List
from loguru import logger
from uuid import uuid4
from fastapi import APIRouter, Form, UploadFile, File, Depends, Body

from agentchat.api.services.agent import AgentService
from agentchat.schema.agent import AgentCreateReq, AgentUpdateReq, AgentSearchReq, AgentDeleteReq
from agentchat.schema.schemas import resp_200, resp_500, UnifiedResponseModel
from agentchat.settings import app_settings
from agentchat.api.services.user import UserPayload, get_login_user

router = APIRouter(tags=["Agent"])

@router.post("/agent", response_model=UnifiedResponseModel)
async def create_agent(
    req: AgentCreateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 判断Agent名称是否重复
        if await AgentService.check_repeat_name(name=req.name, user_id=login_user.user_id):
            return resp_500(message="应用名称重复，请更换一个")
        # 为空的话换成默认的Logo
        if not req.logo_url:
            req.logo_url = app_settings.default_config.get("agent_logo_url")

        result = await AgentService.create_agent(login_user, req)
        return resp_200(data=result)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/agent", response_model=UnifiedResponseModel)
async def get_agent(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        results = await AgentService.get_all_agent_by_user_id(user_id=login_user.user_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/agent", response_model=UnifiedResponseModel)
async def delete_agent(
    req: AgentDeleteReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证用户权限
        await AgentService.verify_user_permission(
            req.agent_id,
            login_user.user_id
        )

        await AgentService.delete_agent_by_id(req.agent_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/agent", response_model=UnifiedResponseModel)
async def update_agent(
    agent_request: AgentUpdateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await AgentService.verify_user_permission(
            agent_request.agent_id,
            login_user.user_id
        )

        update_values = agent_request.model_dump(
            exclude={"agent_id"},
            exclude_none=True
        )

        await AgentService.update_agent(
            agent_id=agent_request.agent_id,
            update_values=update_values,
            user_id=login_user.user_id
        )

        return resp_200()

    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post("/agent/search", response_model=UnifiedResponseModel)
async def search_agent(
    req: AgentSearchReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        results = await AgentService.search_agent_name(
            name=req.name,
            user_id=login_user.user_id
        )
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
