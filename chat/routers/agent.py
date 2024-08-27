from fastapi import FastAPI, Request, APIRouter, Form, UploadFile, File
from database.base import Agent
from type.schemas import resp_200, resp_500
from utils.helpers import check_input
from config.service_config import AGENT_DEFAULT_LOGO, LOGO_PREFIX
from uuid import uuid4

router = APIRouter()

@router.post("/agent")
async def create_agent(name: str = Form(...),
                       description: str = Form(...),
                       parameter: str = Form(...),
                       code: str = Form(...),
                       type: str = Form(None),
                       logoFile: UploadFile = File(...)):
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

@router.get("/agent")
async def get_agent():

    data = Agent.get_agent()
    result = []
    for item in data:
        result.append({"id": item.id,
                       "name": item.name,
                       "description": item.description,
                       "logo": LOGO_PREFIX + item.logo,
                       "parameter": data.patameter,
                       "isCustom": data.isCustom,
                       "code": data.code,
                       "type": data.type,
                       "createTime": data.createTime})

    return resp_200(data = result)

@router.delete("/agent")
async def delete_agent(id: str = Form(...)):

    Agent.delete_agent_by_id(id)
    return resp_200()

@router.put("/agent")
async def update_agent(id: str = Form(...),
                       name: str = Form(...),
                       description: str = Form(...),
                       parameter: str = Form(...),
                       code: str = Form(...),
                       logoFile: UploadFile = File(None)):
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

@router.post("/agent/search")
def search_agent(name: str = Form(...)):
    data = Agent.search_agent_name(name=name)

    result = []
    for item in data:
        result.append({"id": item.id,
                       "name": item.name,
                       "description": item.description,
                       "logo": item.logo,
                       "parameter": item.parameter,
                       "isCustom": item.isCustom,
                       "code": item.code,
                       "type": item.type,
                       "createTime": item.createTime})

    return resp_200(data = result)
