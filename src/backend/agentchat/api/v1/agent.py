from fastapi import APIRouter, Form, UploadFile, File, Depends, Body

from agentchat.api.services.agent import AgentService
from agentchat.schema.agent import CreateAgentRequest, UpdateAgentRequest
from agentchat.schema.schemas import resp_200, resp_500, UnifiedResponseModel
from agentchat.settings import app_settings
from agentchat.prompts.template import code_template, parameter_template
from agentchat.api.services.user import UserPayload, get_login_user
from typing import List
from loguru import logger
from uuid import uuid4

router = APIRouter()

@router.post("/agent", response_model=UnifiedResponseModel)
async def create_agent(agent_request: CreateAgentRequest,
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        # 判断Agent名字是否重复
        if AgentService.check_repeat_name(name=agent_request.name, user_id=login_user.user_id):
            return resp_500(message="The Agent name is repeated, please change it")

        # logo 存到本地
        # uid = uuid4().hex
        # if logoFile is not None:
        #     logo = f"agentchat/img/agent/{uid}.{logoFile.content_type.split("/")[-1]}"
        #     with open(logo, "wb") as file:
        #         file.write(await logoFile.read())
        # else:
        #     logo = app_settings.logo.get("agent")



        AgentService.create_agent(name=agent_request.name,
                                  description=agent_request.description,
                                  logo=agent_request.logo_url,
                                  tool_ids=agent_request.tool_ids,
                                  llm_id=agent_request.llm_id,
                                  mcp_ids=agent_request.mcp_ids,
                                  user_id=login_user.user_id,
                                  knowledge_ids=agent_request.knowledge_ids,
                                  use_embedding=agent_request.use_embedding)
        return resp_200()
    except Exception as err:
        logger.error(f"create agent API error: {err}")
        return resp_500(message=str(err))


@router.get("/agent", response_model=UnifiedResponseModel)
async def get_agent(login_user: UserPayload = Depends(get_login_user)):
    try:
        data = AgentService.get_all_agent_by_user_id(user_id=login_user.user_id)
        result = []
        for item in data:
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo_url": item.logo_url,
                           "tool_ids": item.tool_ids,
                           "mcp_ids": item.mcp_ids,
                           "llm_id": item.llm_id,
                           "is_custom": item.is_custom,
                           "use_embedding": item.use_embedding,
                           "create_time": item.create_time})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"get Agent API error: {err}")
        return resp_500(message=str(err))


@router.delete("/agent", response_model=UnifiedResponseModel)
async def delete_agent(agent_id: str = Form(...),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        return AgentService.delete_agent_by_id(id=agent_id, user_id=login_user.user_id)
    except Exception as err:
        logger.error(f"delete agent API error: {err}")
        return resp_500(message=str(err))


@router.put("/agent", response_model=UnifiedResponseModel)
async def update_agent(agent_request: UpdateAgentRequest,
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        if agent_request.name and AgentService.check_repeat_name(agent_request.name, login_user.user_id):
            return resp_500(message="Agent name repeated, please update Agent name")

        return AgentService.update_agent_by_id(id=agent_request.agent_id,
                                        name=agent_request.name,
                                        description=agent_request.description,
                                        logo_url=agent_request.logo_url,
                                        knowledge_ids=agent_request.knowledge_ids,
                                        user_id=login_user.user_id,
                                        tool_ids=agent_request.tool_ids,
                                        llm_id=agent_request.llm_id,
                                        mcp_ids=agent_request.mcp_ids,
                                        use_embedding=agent_request.use_embedding)

    except Exception as err:
        logger.error(f"update agent API error: {err}")
        return resp_500(message=str(err))


@router.post("/agent/search", response_model=UnifiedResponseModel)
async def search_agent(name: str = Body(..., description="搜索框中的Agent 名称"),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        data = AgentService.search_agent_name(name=name, user_id=login_user.user_id)
        result = []
        for item in data:
            # TODO: 之后是否能改成这样的形式
            # attributes = {
            #     key: getattr(item, key)
            #     for key in dir(item)
            #     if not key.startswith('__') and not callable(getattr(item, key))
            # }
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo_url": item.logo_url,
                           "tool_ids": item.tool_ids,
                           "llm_id": item.llm_id,
                           "mcp_ids": item.mcp_ids,
                           "use_embedding": item.use_embedding,
                           "is_custom": item.is_custom,
                           "create_time": item.create_time})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"search agent API error: {err}")
        return resp_500(message=str(err))


@router.get("/default/code", response_model=UnifiedResponseModel)
async def get_default_code(login_user: UserPayload = Depends(get_login_user)):
    return resp_200(data=code_template)


@router.get("/default/parameter", response_model=UnifiedResponseModel)
async def get_default_parameter(login_user: UserPayload = Depends(get_login_user)):
    return resp_200(data=parameter_template)
