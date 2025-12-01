from fastapi import Request, APIRouter, Depends, Body, Query
from agentchat.api.services.history import HistoryService
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.schemas import resp_200, resp_500, UnifiedResponseModel
from loguru import logger

router = APIRouter(tags=["History"])

@router.get("/history", response_model=UnifiedResponseModel)
async def get_dialog_history(dialog_id: str = Query(..., description="对话的ID", embed=True),
                             login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await HistoryService.get_dialog_history(dialog_id=dialog_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
