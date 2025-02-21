from fastapi import Request, APIRouter, Depends
from api.services.history import HistoryService
from api.services.user import get_login_user, UserPayload
from schema.schemas import resp_200, resp_500, UnifiedResponseModel
from loguru import logger

router = APIRouter()

@router.post("/history", response_model=UnifiedResponseModel)
async def get_dialog_history(request: Request,
                             login_user: UserPayload = Depends(get_login_user)):
    try:
        body = await request.json()
        dialog_id = body.get('dialog_id')
        data = HistoryService.get_dialog_history(dialog_id=dialog_id)

        result = []
        for item in data:
            result.append({"role": item.role,
                           "content": item.content})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"get dialog history API error: {err}")
        return resp_500(message=str(err))
