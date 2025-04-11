import json
from fastapi import APIRouter, Body, UploadFile, File
from api.services.history import HistoryService
from api.services.dialog import DialogService
from api.services.mcp_chat import MCPChatAgent
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/mcp_chat", description="对话接口")
async def chat(user_input: str = Body(description='用户问题'),
               dialog_id: str = Body(description='对话的ID')):
    """与助手进行对话"""

    agent = DialogService.get_agent_by_dialog_id(dialog_id)
    mcp_chat_agent = MCPChatAgent(**agent)

    # 流式输出LLM生成结果
    async def general_generate():
        final_result = ''
        async for one_data in await mcp_chat_agent.ainvoke(user_input, dialog_id):
            final_result += json.loads(one_data)['content']
            yield f"data: {one_data}\n\n"
        yield "data: [DONE]"
        # LLM回答的信息存放到MySQL数据库
        await HistoryService.save_chat_history("assistant", final_result, dialog_id)

    # 将用户问题存放到MySQL数据库
    await HistoryService.save_chat_history("user", user_input, dialog_id)
    # 更新对话窗口的最近使用时间
    DialogService.update_dialog_time(dialog_id)
    return StreamingResponse(general_generate(), media_type="text/event-stream")
