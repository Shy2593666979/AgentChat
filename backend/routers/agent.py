from fastapi import APIRouter, Form, UploadFile, File, Depends

from routers.user import login
from service.agent import AgentService
from type.schemas import resp_200, resp_500, UnifiedResponseModel
from utils.helpers import check_input
from config.service_config import AGENT_DEFAULT_LOGO, LOGO_PREFIX
from prompt.template import code_template, parameter_template
from service.user import UserPayload, get_login_user
from typing import List
from loguru import logger
from uuid import uuid4

router = APIRouter()

@router.post("/agent", response_model=UnifiedResponseModel)
async def create_agent(name: str = Form(...),
                       description: str = Form(...),
                       tool_id: List[str] = Form(None),
                       llm_id: str = Form(None),
                       logoFile: UploadFile = File(...),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        # 判断Agent名字是否重复
        if AgentService.check_repeat_name(name=name):
            return resp_500(message="The Agent name is repeated, please change it")

        uid = uuid4().hex
        if logoFile is not None:
            logo = f"img/{uid}.{logoFile.content_type.split('/')[-1]}"
            with open(logo, 'wb') as file:
                file.write(await logoFile.read())
        else:
            logo = AGENT_DEFAULT_LOGO

        # 保证所有Agents的name都是英文
        if not check_input(user_input=name):
            return resp_500(message="The name parameter can only contain uppercase and lowercase letters and numbers.")

        AgentService.create_agent(name=name,
                                  description=description,
                                  logo=logo,
                                  tool_id=tool_id,
                                  llm_id=llm_id,
                                  user_id=login_user.user_id)
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
                           "logo": LOGO_PREFIX + item.logo,
                           "tool_id": item.tool_id,
                           "llm_id": item.llm_id,
                           "is_custom": item.is_custom,
                           "create_time": item.create_time})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"get agent API error: {err}")
        return resp_500(message=str(err))


@router.delete("/agent", response_model=UnifiedResponseModel)
async def delete_agent(agent_id: str = Form(..., alias="id"),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        return AgentService.delete_agent_by_id(id=agent_id, user_id=login_user.user_id)
    except Exception as err:
        logger.error(f"delete agent API error: {err}")
        return resp_500(message=str(err))


@router.put("/agent", response_model=UnifiedResponseModel)
async def update_agent(agent_id: str = Form(..., alias='id'),
                       name: str = Form(None),
                       description: str = Form(None),
                       tool_id: List[str] = Form(None),
                       llm_id: str = Form(None),
                       logoFile: UploadFile = File(None),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        uid = uuid4().hex
        if logoFile is not None:
            logo = f"img/{uid}.{logoFile.content_type.split('/')[-1]}"
            with open(logo, 'wb') as file:
                file.write(await logoFile.read())
        else:
            logo = None

        # 保证所有Agents的name都是英文
        if not check_input(user_input=name):
            return resp_500(message="The name parameter can only contain uppercase and lowercase letters and numbers.")

        return AgentService.update_agent_by_id(id=agent_id,
                                        name=name,
                                        description=description,
                                        logo=logo,
                                        user_id=login_user.user_id,
                                        tool_id=tool_id,
                                        llm_id=llm_id)

    except Exception as err:
        logger.error(f"update agent API error: {err}")
        return resp_500(message=str(err))


@router.post("/agent/search", response_model=UnifiedResponseModel)
async def search_agent(name: str = Form(...),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        data = AgentService.search_agent_name(name=name, user_id=login_user.user_id)
        result = []
        for item in data:
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo": LOGO_PREFIX + item.logo,
                           "tool_id": item.tool_id,
                           "llm_id": item.llm_id,
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
