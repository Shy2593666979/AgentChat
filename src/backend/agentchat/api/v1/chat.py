import json
from typing import Annotated, List, Union
from urllib.parse import urljoin

from fastapi import APIRouter, Body, UploadFile, File, Depends
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from agentchat.api.services.chat import StreamingAgent, AgentConfig
from agentchat.api.services.history import HistoryService
from agentchat.api.services.dialog import DialogService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.chat_prompt import SYSTEM_PROMPT
from agentchat.schema.chat import ConversationReq
from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.services.rag_handler import RagHandler
from agentchat.settings import app_settings
from agentchat.utils.file_utils import get_aliyun_oss_base_path
from fastapi.responses import StreamingResponse

from agentchat.utils.helpers import combine_user_input

router = APIRouter()

Assistant_Role = "assistant"
User_Role = "user"


@router.post("/chat", description="对话接口")
async def chat(*,
               conversation_req: ConversationReq = Body(description="传递的会话信息"),
               login_user: UserPayload = Depends(get_login_user)):
    """与助手进行对话"""
    config = await DialogService.get_agent_by_dialog_id(dialog_id=conversation_req.dialog_id)
    agent_config = AgentConfig(**config)

    # 初始化对话助手
    chat_agent = StreamingAgent(agent_config)
    await chat_agent.init_agent()

    # 整合User Input
    conversation_req.user_input = combine_user_input(conversation_req.user_input, conversation_req.file_url)

    messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT if agent_config.system_prompt.strip() == "" else agent_config.system_prompt)]
    if agent_config.use_embedding:
        history_messages = await HistoryService.select_history(conversation_req.dialog_id, 10)
    else:
        history_messages = await HistoryService.select_history(conversation_req.dialog_id)
    # messages.extend(history_messages)
    messages[0].content = SYSTEM_PROMPT.format(history=str(history_messages))
    messages.append(HumanMessage(content=conversation_req.user_input))

    events = []
    async def general_generate():
        response_content = ""
        async for event in chat_agent.ainvoke_streaming(messages):
            if event.get("type") == "response_chunk":
                # 响应片段：用data:包裹，JSON格式，双换行结尾
                # chunk_data = {"chunk": event["data"].get("chunk")}
                # yield f'data: {json.dumps(chunk_data)}\n\n'
                yield f'data: {json.dumps(event)}\n\n'
                response_content += event["data"].get("chunk")
            else:
                # 其他事件（如工具调用、心跳）同样按SSE格式输出
                events.append(event)
                yield f'data: {json.dumps(event)}\n\n'
        await HistoryService.save_chat_history(Assistant_Role, response_content, events, conversation_req.dialog_id, agent_config.use_embedding)

    # 将用户问题存放到MySQL数据库
    await HistoryService.save_chat_history(User_Role, conversation_req.user_input, events, conversation_req.dialog_id, agent_config.use_embedding)

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/upload", description="上传文件的接口", response_model=UnifiedResponseModel)
async def upload_file(*,
                      file: UploadFile = File(description="支持常见的Pdf、Docx、Txt、Jpg等文件"),
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        file_content = await file.read()

        oss_object_name = get_aliyun_oss_base_path(file.filename)
        sign_url = urljoin(app_settings.aliyun_oss["base_url"], oss_object_name)

        aliyun_oss.sign_url_for_get(sign_url)
        aliyun_oss.upload_file(oss_object_name, file_content)

        return resp_200(sign_url)
    except Exception as err:
        return resp_500(message=str(err))

@router.post("/knowledge/retrieval", response_model=UnifiedResponseModel)
async def retrieval_knowledge(*,
                              query: str = Body(..., description="用户的问题"),
                              knowledge_id: Union[str, List[str]] = Body(..., description="知识库ID")):
    if isinstance(knowledge_id, str):
        content = await RagHandler.retrieve_ranked_documents(query, [knowledge_id], [knowledge_id])
    else:
        content = await RagHandler.retrieve_ranked_documents(query, knowledge_id, knowledge_id)
    return resp_200(content)