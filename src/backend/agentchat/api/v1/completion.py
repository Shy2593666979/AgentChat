import json
from typing import Callable, List

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger
from starlette.background import BackgroundTask

from agentchat.api.responses.streaming import WatchedStreamingResponse
from agentchat.api.services.conversation import ConversationService
from agentchat.api.services.history import HistoryService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.core.agents.general_agent import AgentConfig, GeneralAgent
from agentchat.prompts.completion import SYSTEM_PROMPT
from agentchat.protocols.ag_ui import protocol_stream
from agentchat.schemas.completion import CompletionReq
from agentchat.services.memory.client import memory_client
from agentchat.services.memory.optional import (
    search_optional_memory,
    store_optional_memory,
)
from agentchat.utils.chat_attachments import attachment_events
from agentchat.utils.common import count_tokens_usage
from agentchat.utils.contexts import (
    set_agent_name_context,
    set_conversation_id_context,
    set_user_id_context,
)
from agentchat.utils.helpers import (
    build_completion_system_prompt,
    build_completion_user_input,
)
from agentchat.utils.logging import bind_log_context

router = APIRouter(tags=["Completion"])

@router.post("/completion", description="对话接口")
async def completion(
    *,
    req: CompletionReq,
    login_user: UserPayload = Depends(get_login_user),
    request: Request = None
):
    """
    实时对话接口（SSE流式）
    """

    # Agent 初始化
    try:
        db_config = await ConversationService.resolve_agent(req.conversation_id, login_user.user_id, req.agent_id)
    except ValueError as error:
        raise HTTPException(status_code=403 if "权限" in str(error) else 400, detail=str(error)) from error
    agent_config = AgentConfig(**db_config)
    agent_config.user_id = login_user.user_id

    # 设置上下文信息
    set_user_id_context(login_user.user_id)
    set_agent_name_context(agent_config.name)
    set_conversation_id_context(req.conversation_id)
    if request is not None:
        bind_log_context(agent_id=db_config["id"])

    raw_input = req.user_input
    # 先读取旧上下文，再保存本轮输入，避免把本轮问题重复放入模型上下文。
    short_history = await HistoryService.get_short_term_messages(req.conversation_id, login_user.user_id)
    history_summary = await ConversationService.get_conversation_history_summary(req.conversation_id)
    saved = await HistoryService.save_chat_history(
        role="user", content=raw_input, events=attachment_events(req), conversation_id=req.conversation_id,
        token_usage=count_tokens_usage(raw_input), memory_enable=False
    )
    if saved["first_user"]:
        ConversationService.queue_conversation_title(req.conversation_id, raw_input, saved["title"])

    # 标题已独立启动，主流程直接初始化本轮智能体，不等待标题结果。
    chat_agent = GeneralAgent(agent_config)
    await chat_agent.init_agent()

    # 输入处理
    user_input = build_completion_user_input(
        file_url=req.file_url,
        user_input=raw_input
    )

    # Prompt 构建
    system_prompt = agent_config.system_prompt.strip() or SYSTEM_PROMPT

    long_memory = None
    memory_available = False
    if agent_config.enable_memory:
        long_memory, memory_available = await search_optional_memory(
            memory_client, query=raw_input, run_id=req.conversation_id
        )

    system_prompt = build_completion_system_prompt(
        system_prompt,
        history_summary,
        long_memory
    )

    messages: List[BaseMessage] = [
        SystemMessage(content=system_prompt),
        *short_history,
        HumanMessage(content=user_input),
    ]

    # 事件 & 流式响应
    # 身份随本次请求固定，切换智能体不会改变正在生成的回复或过去的回复。
    agent_event = {
        "type": "agent",
        "data": {
            "agent_id": db_config["id"],
            "name": db_config["name"],
            "logo_url": db_config.get("logo_url", ""),
        },
    }
    events: list = [agent_event]
    response_content = ""
    completed = False

    async def stream():
        nonlocal response_content, completed
        agent_stream = chat_agent.astream(messages)
        try:
            yield f"data: {json.dumps(agent_event, ensure_ascii=False)}\n\n"
            if agent_config.enable_memory and not memory_available:
                event = {
                    'type': 'event',
                    'data': {
                        'status': 'ERROR',
                        'title': '长期记忆暂不可用',
                        'message': '本次继续使用当前会话上下文，聊天记录会正常保存。',
                    },
                }
                events.append(event)
                yield f"data: {json.dumps(event)}\n\n"
            async for event in agent_stream:

                if event.get("type") == "response_chunk":
                    chunk = event["data"].get("chunk", "")
                    response_content += chunk
                else:
                    events.append(event)

                yield f"data: {json.dumps(event)}\n\n"

            completed = True
        finally:
            import anyio
            # 停止生成也保存已收到的回复，取消作用域不能中断数据库写入。
            with anyio.CancelScope(shield=True):
                await agent_stream.aclose()
                await HistoryService.save_chat_history(
                    role="assistant", content=response_content, events=events, conversation_id=req.conversation_id,
                    token_usage=count_tokens_usage(response_content), memory_enable=memory_available
                )

    async def after_response():
        # 正文和历史保存完成即可结束发送，辅助模型调用不占用 SSE 连接。
        if not completed:
            return
        try:
            if memory_available:
                await store_optional_memory(
                    memory_client,
                    messages=[
                        {"role": "user", "content": raw_input},
                        {"role": "assistant", "content": response_content},
                    ],
                    run_id=req.conversation_id,
                )
            await ConversationService.update_conversation_summary(conversation_id=req.conversation_id, user_id=login_user.user_id)
        except Exception:
            logger.exception("对话后续记忆或摘要处理失败")

    # 返回流式响应
    return WatchedStreamingResponse(
        content=protocol_stream(stream(), request, "conversation", req.conversation_id),
        callback=chat_agent.stop_streaming_callback,
        media_type="text/event-stream",
        background=BackgroundTask(after_response),
    )
