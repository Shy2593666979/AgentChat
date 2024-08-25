from fastapi import FastAPI, Request, APIRouter
from database.base import HistoryMessage
from type.schemas import resp_200

router = APIRouter()

@router.get("/history")
async def get_dialog_history(request: Request):
    body = await request.json()

    dialogId = body.get('dialogId')
    data = HistoryMessage.get_dialog_history(dialogId=dialogId)

    result = []
    for item in data:
        result.append({"role": item.role,
                       "content": item.content})

    return resp_200(data=result)
