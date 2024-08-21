from fastapi import FastAPI, Request, APIRouter
from chat.database.base import Agent
from chat.type.schemas import resp_200

router = APIRouter()

@router.post("/agent")
async def create_agent(request: Request):
    body = await request.json()

    name = body.get('name')
    description = body.get('description')
    parameter = body.get('parameter')
    type = body.get('type')
    code = body.get('code')

    Agent.create_agent(name=name, description=description, parameter=parameter, code=code, type=type if type is not None else "openai")

    return resp_200()

@router.get("/agent")
async def get_agent():

    data = Agent.get_agent()
    result = []
    for item in data:
        result.append({"id": item.id, "name": item.name, "description": item.description, "parameter": data.patameter, "type": data.type, "createTime": data.createTime})
    return resp_200(data = result)


