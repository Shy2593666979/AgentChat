from fastapi import APIRouter, Depends, Query
from loguru import logger

from agentchat.api.responses.builder import UnifiedResponseModel, resp_200, resp_500
from agentchat.api.services.conversation import ConversationService
from agentchat.api.services.history import HistoryService
from agentchat.api.services.user import UserPayload, get_login_user

router = APIRouter(tags=["History"])

@router.get("/history", response_model=UnifiedResponseModel)
async def get_conversation_history(conversation_id: str = Query(..., description="对话的ID", embed=True),
                             login_user: UserPayload = Depends(get_login_user)):
    try:
        await ConversationService.verify_user_permission(conversation_id, login_user.user_id)
        results = await HistoryService.get_conversation_history(conversation_id=conversation_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
