from fastapi import FastAPI, Request, APIRouter, Form, UploadFile, File
from chat.database.base import Agent
from chat.type.schemas import resp_200, resp_500
from chat.utils.helpers import check_input
from chat.config.service_config import AGENT_DEFAULT_LOGO
from uuid import uuid4

router = APIRouter()

@router.post("/agent")
async def create_agent(name: str = Form(...),
                       description: str = Form(...),
                       parameter: str = Form(...),
                       code: str = Form(...),
                       type: str = Form(None),
                       logoFile: UploadFile = File(...)):
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

    Agent.create_agent(name=name, description=description, logo=logo, parameter=parameter, code=code, type=type if type is not None else "openai")
    return resp_200()

@router.get("/agent")
async def get_agent():

    data = Agent.get_agent()
    result = []
    for item in data:
        result.append({"id": item.id, "name": item.name, "description": item.description, "parameter": data.patameter, "type": data.type, "createTime": data.createTime})
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

    Agent.update_agent_by_id(id=id, name=name, description=description, logo=logo, parameter=parameter, code=code)
    return resp_200()
