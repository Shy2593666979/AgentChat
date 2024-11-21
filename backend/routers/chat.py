from fastapi import Request, APIRouter
import json
from service.history import HistoryService
from service.dialog import DialogService
from chat.client import ChatClient
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/chat", description="对话接口")
async def chat(request: Request):
    """与助手进行对话"""
    body = await request.json()
    dialog_id = body.get('dialog_id')
    user_input = body.get('user_input')

    chat_client = ChatClient(dialog_id=dialog_id)

    # 流式输出LLM生成结果
    async def general_generate():
        final_result = ''
        async for one_data in chat_client.send_response(user_input=user_input):
            final_result += json.loads(one_data)['content']
            yield f"data: {one_data}\n\n"
        yield "data: [DONE]"
        # LLM回答的信息存放到MySQL数据库
        HistoryService.create_history(role="assistant", content=final_result, dialog_id=dialog_id)
    
    # 将用户问题存放到MySQL数据库
    HistoryService.create_history(role="user", content=user_input, dialog_id=dialog_id)
    # 更新对话窗口的最近使用时间
    DialogService.update_dialog_time(dialog_id=dialog_id)
    return StreamingResponse(general_generate(), media_type="text/event-stream")
