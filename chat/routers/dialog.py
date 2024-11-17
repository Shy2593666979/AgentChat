from loguru import logger
from fastapi import  APIRouter, Request
from service.agent import AgentService
from service.dialog import DialogService
from type.schemas import resp_200, resp_500
from config.service_config import LOGO_PREFIX

router = APIRouter()

@router.get("/dialog/list", description="获取对话列表")
async def get_dialog():
    try:
        data = DialogService.get_list_dialog()
        result = []
        for msg in data:
            msg_agent = AgentService.select_agent_by_name(name=msg.agent)
            result.append({"name": msg.name,
                           "agent": msg.agent,
                           "dialog_id": msg.dialog_id,
                           "create_time": msg.create_time,
                           "logo": LOGO_PREFIX + msg_agent[0].logo})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"get dialog API error: {err}")
        return resp_500(message=str(err))


@router.post("/dialog", description="创建对话窗口")
async def create_dialog(request: Request):
    try:
        body = await request.json()
        name = body.get('name')
        agent = body.get('agent')

        dialog_id = DialogService.create_dialog(name if name is not None else agent, agent)

        return resp_200(data={"dialog_id": dialog_id})
    except Exception as err:
        logger.error(f"create dialog API error: {err}")
        return resp_500(message=str(err))

@router.delete("/dialog", description="删除对话窗口")
async def delete_dialog(request: Request):
    try:
        body = await request.json()
        dialog_id = body.get('dialog_id')

        DialogService.delete_dialog(dialog_id=dialog_id)

        return resp_200()
    except Exception as err:
        logger.error(f"delete dialog API error: {err}")
        return resp_500(message=str(err))
