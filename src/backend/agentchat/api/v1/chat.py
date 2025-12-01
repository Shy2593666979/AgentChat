import json
import loguru
from starlette.types import Receive
from typing import Annotated, List, Union, Callable
from fastapi import APIRouter, Body, UploadFile, File, Depends
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from agentchat.api.services.chat import StreamingAgent, AgentConfig
from agentchat.api.services.history import HistoryService
from agentchat.api.services.dialog import DialogService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.chat import SYSTEM_PROMPT
from agentchat.schema.chat import ConversationReq
from agentchat.services.memory.client import memory_client
from agentchat.utils.contexts import set_user_id_context, set_agent_name_context
from fastapi.responses import StreamingResponse

from agentchat.utils.helpers import combine_user_input, combine_history_messages

router = APIRouter(tags=["Completion"])

"""
重写 StreamingResponse类 保证流式输出的时候可随时暂停
"""
class WatchedStreamingResponse(StreamingResponse):
    def __init__(self,
                 content,
                 callback: Callable = None,
                 status_code: int = 200,
                 headers = None,
                 media_type: str | None = None,
                 background = None,
                 ):
        super().__init__(content, status_code, headers, media_type, background)

        self.callback = callback

    async def listen_for_disconnect(self, receive: Receive) -> None:
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                loguru.logger.info("http.disconnect. stop task and streaming")

                if self.callback:
                    self.callback()

                break

@router.post("/chat", description="对话接口")
async def chat(*,
               conversation_req: ConversationReq = Body(description="传递的会话信息"),
               login_user: UserPayload = Depends(get_login_user)):
    """
    与AI助手进行实时对话的核心接口
    
    该接口支持流式响应，能够实时返回AI生成的内容，
    同时处理历史对话记录和上下文管理
    """
    # 根据对话ID获取智能体配置信息
    config = await DialogService.get_agent_by_dialog_id(dialog_id=conversation_req.dialog_id)
    agent_config = AgentConfig(**config)

    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(agent_config.name)

    # 将agent_config的配置改成请求的用户ID
    agent_config.user_id = login_user.user_id
    # 基于配置创建流式对话智能体实例
    chat_agent = StreamingAgent(agent_config)
    await chat_agent.init_agent()

    # 备份用户原始输入，用于后续数据库存储和记忆检索
    original_user_input = conversation_req.user_input
    # 整合用户输入内容，将文本和附件URL合并处理
    conversation_req.user_input = combine_user_input(conversation_req.user_input, conversation_req.file_url)

    # 构建对话消息列表，首先添加系统提示词作为基础指令
    messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT if agent_config.system_prompt.strip() == "" else agent_config.system_prompt)]
    if agent_config.enable_memory:
        # 启用向量化记忆模式：通过语义搜索获取相关历史上下文
        history_messages = await memory_client.search(query=original_user_input, run_id=conversation_req.dialog_id)
        messages[0].content = SYSTEM_PROMPT.format(history=f"<chat_history>\n {'\n'.join(msg.get('memory', '') for msg in history_messages.get('results'))} </chat_history>")
    else:
        # 传统历史记录模式：从数据库获取完整对话历史并融入系统提示词
        history_messages = await HistoryService.select_history(conversation_req.dialog_id)
        messages[0].content = SYSTEM_PROMPT.format(history=combine_history_messages(history_messages))
    # 添加当前用户输入作为人类消息
    messages.append(HumanMessage(content=conversation_req.user_input))

    # 事件收集器，用于记录工具调用等非响应内容的事件
    events = []
    async def general_generate():
        """
        流式响应生成器
        
        实时处理AI助手的响应流，将内容按SSE格式返回给前端，
        同时收集和处理各种事件（工具调用、心跳等）
        """
        response_content = " "
        try:
            async for event in chat_agent.astream(messages):
                if event.get("type") == "response_chunk":
                    # 处理AI生成的文本片段：按SSE标准格式封装并流式传输
                    yield f'data: {json.dumps(event)}\n\n'
                    response_content += event["data"].get("chunk")
                else:
                    # 处理其他类型事件（工具调用、状态更新等）：记录并同样流式传输
                    events.append(event)
                    yield f'data: {json.dumps(event)}\n\n'
        finally:
            if agent_config.enable_memory: # 将完整的助手回复保存到记忆系统，在流式输出完，不影响响应时间
                await memory_client.add([{"role": "user", "content": original_user_input}, {"role": "assistant", "content": response_content}], run_id=conversation_req.dialog_id)
            # 将助手回复及相关事件持久化到数据库
            await HistoryService.save_chat_history("assistant", response_content, events, conversation_req.dialog_id, agent_config.enable_memory)

    # 将用户输入持久化到MySQL数据库，用于历史对话记录展示
    await HistoryService.save_chat_history("user", original_user_input, events, conversation_req.dialog_id, agent_config.enable_memory)

    # 返回SSE流式响应，支持实时前端交互
    return WatchedStreamingResponse(general_generate(), callback=chat_agent.stop_streaming_callback, media_type="text/event-stream")
