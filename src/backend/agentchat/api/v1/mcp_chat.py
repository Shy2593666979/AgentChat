import json
from fastapi import APIRouter, Body, UploadFile, File
from agentchat.api.services.history import HistoryService
from agentchat.api.services.dialog import DialogService
from agentchat.api.services.mcp_chat import MCPChatAgent
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["MCP-Chat"])

# 前端根据Dialog.agent_type判断走/mcp_chat 还是/chat
@router.post("/mcp_chat", description="对话接口")
async def chat(user_input: str = Body(description='用户问题'),
               dialog_id: str = Body(description='对话的ID')):
    """与助手进行对话"""

    agent = await DialogService.get_agent_by_dialog_id(dialog_id)
    mcp_chat_agent = MCPChatAgent(**agent)
    await mcp_chat_agent.init_MCP_Server()

    # 流式输出LLM生成结果
    async def general_generate():
        assistant_result = ""
        async for text in await mcp_chat_agent.ainvoke(user_input, dialog_id, True):
            assistant_result += text
            yield f"{text}\n\n"
        yield "[DONE]"
        await HistoryService.save_chat_history("assistant", assistant_result, dialog_id)

    await HistoryService.save_chat_history("user", user_input, dialog_id)
    # 更新对话窗口的最近使用时间
    DialogService.update_dialog_time(dialog_id)
    return StreamingResponse(general_generate(), media_type="text/event-stream")
