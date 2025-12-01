from loguru import logger
from fastapi import APIRouter, Depends, Body
from agentchat.api.services.agent import AgentService
from agentchat.api.services.dialog import DialogService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schema.dialog import DialogCreateRequest
from agentchat.schema.schemas import resp_200, resp_500, UnifiedResponseModel
from agentchat.settings import app_settings

router = APIRouter(tags=["Dialog"])


@router.get("/dialog/list", response_model=UnifiedResponseModel)
async def get_dialog(login_user: UserPayload = Depends(get_login_user)):
    try:
        messages = await DialogService.get_list_dialog(user_id=login_user.user_id)
        results = []
        for msg in messages:
            msg_agent = await AgentService.select_agent_by_id(agent_id=msg["agent_id"])

            msg.update(msg_agent)
            results.append(msg)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post("/dialog", response_model=UnifiedResponseModel)
async def create_dialog(dialog_req: DialogCreateRequest = Body(),
                        login_user: UserPayload = Depends(get_login_user)):
    try:
        dialog = await DialogService.create_dialog(name=dialog_req.name, agent_id=dialog_req.agent_id,
                                                   agent_type=dialog_req.agent_type, user_id=login_user.user_id)
        print(dialog)
        return resp_200(dialog)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/dialog", response_model=UnifiedResponseModel)
async def delete_dialog(dialog_id: str = Body(description="对话ID", embed=True),
                        login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await DialogService.verify_user_permission(dialog_id, login_user.user_id)

        await DialogService.delete_dialog(dialog_id=dialog_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
