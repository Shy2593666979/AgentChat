from fastapi import Request, APIRouter

from database.base import HistoryMessage
from processor.chat_bot import ChatbotModel

router = APIRouter()

@router.post("/chat", description="对话接口")
async def chat(request: Request):
    """需要dialogId"""
    body = await request.json()
    dialogId = body.get('dialogId')
    user_input = body.get('user_input')

    #breakpoint()
    # 根据dialogId 去MySQL数据库查最近K条数据
    chat_bot = ChatbotModel()
    SQL_Message = HistoryMessage.select_history(dialogId)

    for msg in SQL_Message:
        chat_bot.include_history_message(msg)

    response = chat_bot.run(user_input, chat_bot.get_history_message())

    # 将用户问的存放到MySQL数据库
    HistoryMessage.create_history(role="user", content=user_input, dialogId=dialogId)
    # LLM回答的信息存放到MySQL数据库
    HistoryMessage.create_history(role="assistant", content=response, dialogId=dialogId)
    return response