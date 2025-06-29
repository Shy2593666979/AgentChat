import json
from typing import Annotated, List
from urllib.parse import urljoin

from fastapi import APIRouter, Body, UploadFile, File, Depends
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from agentchat.api.services.chat import ChatAgent, AgentConfig
from agentchat.api.services.history import HistoryService
from agentchat.api.services.dialog import DialogService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schema.chat import ConversationReq
from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.services.chat.client import ChatClient
from agentchat.settings import app_settings
from agentchat.utils.file_utils import get_aliyun_oss_base_path
from fastapi.responses import StreamingResponse

router = APIRouter()

Assistant_Role = "assistant"
User_Role = "user"

SYSTEM_PROMPT = """
你是一个智能助手，请根据用户的问题进行回复。请严格遵守以下要求：
✅ 回复原则
    - 根据用户提出的问题，提供准确、有用、礼貌 的信息。
    - 所有回答必须符合法律法规和社会伦理标准。
    - 不得生成任何高危言论、违法信息或不当内容 。
⚠️ 内容安全限制
    禁止涉及但不限于以下内容：
    - 涉及暴力、色情、赌博、毒品等相关信息；
    - 政治敏感话题；
    - 侵犯他人隐私或版权的内容；
    - 其他违反国家法律法规的内容。
🛠️ 工具调用说明
    - 如果问题需要调用外部工具（如天气查询、Google搜索等），请参考相关工具文档进行处理。
    - 在回复中应明确标注是否调用了工具，并简要说明结果来源。
"""


# 前端根据Dialog.agent_type判断走/mcp_chat 还是/chat
@router.post("/chat", description="对话接口")
async def chat(*,
               conversation_req: ConversationReq = Body(description="传递的会话信息"),
               login_user: UserPayload = Depends(get_login_user)):
    """与助手进行对话"""
    config = await DialogService.get_agent_by_dialog_id(dialog_id=conversation_req.dialog_id)
    agent_config = AgentConfig(**config)

    # 初始化对话助手
    chat_agent = ChatAgent(agent_config)
    await chat_agent.init_agent()

    messages: List[BaseMessage] = [HumanMessage(content=conversation_req.use_input), SystemMessage(
        content=SYSTEM_PROMPT if agent_config.system_prompt.strip() == "" else agent_config.system_prompt)]
    if agent_config.use_embedding:
        history_messages = await HistoryService.select_history(conversation_req.dialog_id, 10)
    else:
        history_messages = await HistoryService.select_history(conversation_req.dialog_id)
    messages.extend(history_messages)

    async def general_generate():
        final_content = ""
        async for chunk_content in chat_agent.ainvoke(messages):
            final_content += chunk_content
            yield f"data: {chunk_content}\n\n"
        yield "data: [DONE]"
        await HistoryService.save_chat_history(Assistant_Role, final_content, conversation_req.dialog_id)

    # 将用户问题存放到MySQL数据库
    await HistoryService.save_chat_history(User_Role, conversation_req.user_input, conversation_req.dialog_id)

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/upload", description="上传文件的接口", response_model=UnifiedResponseModel)
async def upload_file(*,
                      file: UploadFile = File(description="支持常见的Pdf、Docx、Txt、Jpg等文件"),
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        file_content = await file.read()

        oss_base_path = get_aliyun_oss_base_path(file.filename)
        sign_url = urljoin(app_settings.aliyun_oss["base_url"], oss_base_path)

        aliyun_oss.sign_url_for_get(sign_url)
        aliyun_oss.upload_file(sign_url, file_content)

        return resp_200(message=sign_url)
    except Exception as err:
        return resp_500(message=str(err))

