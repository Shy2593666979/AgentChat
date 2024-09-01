from fastapi import FastAPI, Request, APIRouter, Form, UploadFile, File
from database.base import Agent
from type.schemas import resp_200, resp_500
from utils.helpers import check_input
from config.service_config import AGENT_DEFAULT_LOGO, LOGO_PREFIX
from prompt.template import code_template, parameter_template
from loguru import logger
from uuid import uuid4

router = APIRouter()

@router.post("/agent")
async def create_agent(name: str = Form(...),
                       description: str = Form(...),
                       parameter: str = Form(...),
                       code: str = Form(...),
                       type: str = Form(None),
                       logoFile: UploadFile = File(...)):
    try:
        # 判断Agent名字是否重复
        if Agent.check_repeat_name(name=name):
            return resp_500(message="The Agent name is repeated, please change it")

        uid = uuid4().hex
        if logoFile is not None:
            logo = f"img/{uid}.{logoFile.content_type.split('/')[-1]}"
            with open(logo, 'wb') as file:
                file.write(await logoFile.read())
        else:
            logo = AGENT_DEFAULT_LOGO

        # 保证所有Agents的name都是英文
        if not check_input(userInput=name):
            return resp_500(message="The name parameter can only contain uppercase and lowercase letters and numbers.")

        Agent.create_agent(name=name,
                           description=description,
                           logo=logo,
                           parameter=parameter,
                           code=code,
                           type=type if type is not None else "openai")
        return resp_200()
    except Exception as err:
        logger.error(f"create agent API error: {err}")
        return resp_500(message=str(err))

@router.get("/agent")
async def get_agent():
    try:
        data = Agent.get_agent()
        result = []
        for item in data:
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo": LOGO_PREFIX + item.logo,
                           "parameter": item.parameter,
                           "isCustom": item.isCustom,
                           "code": item.code,
                           "type": item.type,
                           "createTime": item.createTime})

        return resp_200(data = result)
    except Exception as err:
        logger.error(f"get agent API error: {err}")
        return resp_500(message=str(err))


@router.delete("/agent")
async def delete_agent(id: str = Form(...)):
    try:
        Agent.delete_agent_by_id(id)
        return resp_200()
    except Exception as err:
        logger.error(f"delete agent API error: {err}")
        return resp_500(message=str(err))

@router.put("/agent")
async def update_agent(id: str = Form(...),
                       name: str = Form(None),
                       description: str = Form(None),
                       parameter: str = Form(None),
                       code: str = Form(None),
                       logoFile: UploadFile = File(None)):
    try:
        uid = uuid4().hex
        if logoFile is not None:
            logo = f"img/{uid}.{logoFile.content_type.split('/')[-1]}"
            with open(logo, 'wb') as file:
                file.write(await logoFile.read())
        else:
            logo = None

        # 保证所有Agents的name都是英文
        if not check_input(userInput=name):
            return resp_500(message="The name parameter can only contain uppercase and lowercase letters and numbers.")

        Agent.update_agent_by_id(id=id,
                                 name=name,
                                 description=description,
                                 logo=logo,
                                 parameter=parameter,
                                 code=code)

        return resp_200()
    except Exception as err:
        logger.error(f"update agent API error: {err}")
        return resp_500(message=str(err))

@router.post("/agent/search")
async def search_agent(name: str = Form(...)):
    try:
        data = Agent.search_agent_name(name=name)
        result = []
        for item in data:
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo": LOGO_PREFIX + item.logo,
                           "parameter": item.parameter,
                           "isCustom": item.isCustom,
                           "code": item.code,
                           "type": item.type,
                           "createTime": item.createTime})

        return resp_200(data = result)
    except Exception as err:
        logger.error(f"search agent API error: {err}")
        return resp_500(message=str(err))

@router.get("/default/code")
async def get_default_code():
    return resp_200(data = code_template)

@router.get("/default/parameter")
async def get_default_parameter():
    return resp_200(data = parameter_template)
