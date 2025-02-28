import json
from typing import Annotated
from fastapi import APIRouter, Body, UploadFile, File
from api.services.history import HistoryService
from api.services.dialog import DialogService
from services.chat.client import ChatClient
from utils.file_utils import save_upload_file, read_upload_file
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/chat", description="对话接口")
async def chat(file: UploadFile = File(None),
               user_input: str = Body(description='用户问题'),
               dialog_id: str = Body(description='对话的ID')):
    """与助手进行对话"""

    chat_client = ChatClient(dialog_id=dialog_id)

    if file:
        file_path = await save_upload_file(file)
        file_content = await read_upload_file(file_path)
        user_input += f"上传的文件路径为：{file_path}"

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
