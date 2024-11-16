from fastapi import Request, APIRouter
from service.history import HistoryService
from type.schemas import resp_200, resp_500
from loguru import logger

router = APIRouter()


@router.post("/history")
async def get_dialog_history(request: Request):
    try:
        body = await request.json()
        dialogId = body.get('dialogId')
        data = HistoryService.get_dialog_history(dialogId=dialogId)

        result = []
        for item in data:
            result.append({"role": item.role,
                           "content": item.content})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"get dialog history API error: {err}")
        return resp_500(message=str(err))
