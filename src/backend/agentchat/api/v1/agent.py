from fastapi import APIRouter, Form, UploadFile, File, Depends, Body

from agentchat.api.services.agent import AgentService
from agentchat.api.v1.chat import SYSTEM_PROMPT
from agentchat.schema.agent import CreateAgentRequest, UpdateAgentRequest
from agentchat.schema.schemas import resp_200, resp_500, UnifiedResponseModel
from agentchat.settings import app_settings
from agentchat.api.services.user import UserPayload, get_login_user
from typing import List
from loguru import logger
from uuid import uuid4

router = APIRouter(tags=["Agent"])


@router.post("/agent", response_model=UnifiedResponseModel)
async def create_agent(agent_request: CreateAgentRequest = Body(),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        # 判断Agent名称是否重复
        if await AgentService.check_repeat_name(name=agent_request.name, user_id=login_user.user_id):
            return resp_500(message="应用名称重复，请更换一个吧~")
        # 为空的话换成默认的Logo
        if agent_request.logo_url == "":
            agent_request.logo_url = app_settings.default_config.get("agent_logo_url")

        await AgentService.create_agent(name=agent_request.name,
                                        description=agent_request.description,
                                        logo_url=agent_request.logo_url,
                                        tool_ids=agent_request.tool_ids,
                                        llm_id=agent_request.llm_id,
                                        mcp_ids=agent_request.mcp_ids,
                                        user_id=login_user.user_id,
                                        system_prompt=agent_request.system_prompt,
                                        knowledge_ids=agent_request.knowledge_ids,
                                        enable_memory=agent_request.enable_memory)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/agent", response_model=UnifiedResponseModel)
async def get_agent(login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await AgentService.get_all_agent_by_user_id(user_id=login_user.user_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/agent", response_model=UnifiedResponseModel)
async def delete_agent(agent_id: str = Body(..., description="删除的Agent ID", embed=True),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await AgentService.verify_user_permission(agent_id, login_user.user_id)

        await AgentService.delete_agent_by_id(agent_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/agent", response_model=UnifiedResponseModel)
async def update_agent(agent_request: UpdateAgentRequest,
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await AgentService.verify_user_permission(agent_request.agent_id, login_user.user_id)

        await AgentService.update_agent_by_id(id=agent_request.agent_id,
                                              name=agent_request.name,
                                              description=agent_request.description,
                                              logo_url=agent_request.logo_url,
                                              knowledge_ids=agent_request.knowledge_ids,
                                              user_id=login_user.user_id,
                                              tool_ids=agent_request.tool_ids,
                                              llm_id=agent_request.llm_id,
                                              mcp_ids=agent_request.mcp_ids,
                                              system_prompt=agent_request.system_prompt,
                                              enable_memory=agent_request.enable_memory)
        return resp_200()

    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post("/agent/search", response_model=UnifiedResponseModel)
async def search_agent(name: str = Body(..., description="搜索框中的Agent 名称", embed=True),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await AgentService.search_agent_name(name=name, user_id=login_user.user_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
