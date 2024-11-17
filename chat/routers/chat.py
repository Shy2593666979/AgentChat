from fastapi import Request, APIRouter

from service.history import HistoryService
from service.dialog import DialogService
from processor.chat_bot import ChatbotModel
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/chat", description="对话接口")
async def chat(request: Request):
    """需要dialog_id"""
    body = await request.json()
    dialog_id = body.get('dialog_id')
    user_input = body.get('user_input')
    agent_data = DialogService.get_agent_by_dialog_id(dialog_id)
    agent = agent_data[0].agent

    # breakpoint()

    # 根据dialog_id 去MySQL数据库查最近K条数据
    chat_bot = ChatbotModel()
    SQL_Message = HistoryService.select_history(dialog_id)

    for msg in SQL_Message:
        chat_bot.include_history_message(msg)

    # response = chat_bot.run(user_input, chat_bot.get_history_message(), agent)
    # 流式输出LLM生成结果
    async def general_generate():
        async for one_data in chat_bot.run(user_input, chat_bot.get_history_message(), agent):
            yield f"data: {one_data}\n\n"
        yield "data: [DONE]"
        # LLM回答的信息存放到MySQL数据库
        HistoryService.create_history(role="assistant", content=chat_bot.final_result, dialog_id=dialog_id)
    
    # 将用户问的存放到MySQL数据库
    HistoryService.create_history(role="user", content=user_input, dialog_id=dialog_id)
    # 更新对话窗口的最近使用时间
    DialogService.update_dialog_time(dialog_id=dialog_id)
    return StreamingResponse(general_generate(), media_type="text/event-stream")
