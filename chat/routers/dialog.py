from fastapi import  APIRouter, Request
from database.base import DialogChat
from type.schemas import resp_200, resp_500

router = APIRouter()

@router.get("/dialog/list", description="获取对话列表")
async def get_dialog():
    data = DialogChat.get_list_dialog()
    result = []
    for msg in data:
        result.append({"dialogId": msg.dialogId, "name": msg.name, "agent": msg.agent})
    return resp_200(data=result)

@router.post("/dialog", description="创建对话窗口")
async def create_dialog(request: Request):
    body = await request.json()
    name = body.get('name')
    agent = body.get('agent')

    dialogId = DialogChat.create_dialog(name, agent)

    return resp_200(data={"dialogId": dialogId})