from fastapi import Request, APIRouter

from database.base import HistoryMessage, DialogChat, Agent
from processor.chat_bot import ChatbotModel
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/chat", description="对话接口")
async def chat(request: Request):
    """需要dialogId"""
    body = await request.json()
    dialogId = body.get('dialogId')
    user_input = body.get('userInput')
    agent = body.get('agent')

    # breakpoint()

    # 根据dialogId 去MySQL数据库查最近K条数据
    chat_bot = ChatbotModel()
    SQL_Message = HistoryMessage.select_history(dialogId)

    for msg in SQL_Message:
        chat_bot.include_history_message(msg)

    # response = chat_bot.run(user_input, chat_bot.get_history_message(), agent)
    # 流式输出LLM生成结果
    async def general_generate():
        async for one_data in chat_bot.run(user_input, chat_bot.get_history_message(), agent):
            yield f"data: {one_data}\n\n"
        yield "data: [DONE]"
        # LLM回答的信息存放到MySQL数据库
        HistoryMessage.create_history(role="assistant", content=chat_bot.final_result, dialogId=dialogId)
    
    # 将用户问的存放到MySQL数据库
    HistoryMessage.create_history(role="user", content=user_input, dialogId=dialogId)
    # 更新对话窗口的最近使用时间
    DialogChat.update_dialog_time(dialogId=dialogId)
    return StreamingResponse(general_generate(), media_type="text/event-stream")
