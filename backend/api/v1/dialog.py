from loguru import logger
from fastapi import APIRouter, Depends, Body
from api.services.agent import AgentService
from api.services.dialog import DialogService
from api.services.user import UserPayload, get_login_user
from schema.schemas import resp_200, resp_500, UnifiedResponseModel
from settings import app_settings

router = APIRouter()


@router.get("/dialog/list", response_model=UnifiedResponseModel)
async def get_dialog(login_user: UserPayload = Depends(get_login_user)):
    try:
        data = DialogService.get_list_dialog(user_id=login_user.user_id)
        result = []
        for msg in data:
            msg_agent = AgentService.select_agent_by_id(agent_id=msg.agent_id)
            result.append({"name": msg.name,
                           "user_id": msg.user_id,
                           "agent_id": msg.agent_id,
                           "agent_type": msg.agent_type,
                           "dialog_id": msg.dialog_id,
                           "create_time": msg.create_time,
                           "logo": app_settings.logo.get("prefix") + msg_agent[0].logo})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"Get dialog API error: {err}")
        return resp_500(message=str(err))


@router.post("/dialog", response_model=UnifiedResponseModel)
async def create_dialog(name: str = Body(description='对话Agent名称'),
                        agent_id: str = Body(description='对话Agent的ID'),
                        agent_type: str = Body(description="Agent的类型，仅支持MCPAgent or Agent"),
                        login_user: UserPayload = Depends(get_login_user)):
    try:
        dialog_id = DialogService.create_dialog(name=name, agent_id=agent_id, agent_type=agent_type,
                                                user_id=login_user.user_id)
        return resp_200(data={"dialog_id": dialog_id})
    except Exception as err:
        logger.error(f"create dialog API error: {err}")
        return resp_500(message=str(err))


@router.delete("/dialog", response_model=UnifiedResponseModel)
async def delete_dialog(dialog_id: str = Body(description='对话ID')):
    try:
        DialogService.delete_dialog(dialog_id=dialog_id)
        return resp_200()
    except Exception as err:
        logger.error(f"delete dialog API error: {err}")
        return resp_500(message=str(err))
