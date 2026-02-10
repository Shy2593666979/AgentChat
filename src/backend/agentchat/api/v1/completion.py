import json
import loguru
from starlette.types import Receive
from fastapi.responses import StreamingResponse
from typing import List, Callable
from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from agentchat.core.agents.general_agent import GeneralAgent, AgentConfig
from agentchat.api.services.history import HistoryService
from agentchat.api.services.dialog import DialogService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.completion import SYSTEM_PROMPT
from agentchat.schema.completion import CompletionReq
from agentchat.services.memory.client import memory_client
from agentchat.utils.contexts import set_user_id_context, set_agent_name_context
from agentchat.utils.helpers import build_completion_system_prompt, build_completion_history_messages, build_completion_user_input

router = APIRouter(tags=["Completion"])

class WatchedStreamingResponse(StreamingResponse):
    """
    重写 StreamingResponse类 保证流式输出的时候可随时暂停
    """
    def __init__(
        self,
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

@router.post("/completion", description="对话接口")
async def completion(
    *,
    req: CompletionReq,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    与AI助手进行实时对话的核心接口

    该接口支持流式响应，能够实时返回AI生成的内容，
    同时处理历史对话记录和上下文管理
    """
    # 根据对话ID获取智能体配置信息
    db_config = await DialogService.get_agent_by_dialog_id(dialog_id=req.dialog_id)
    agent_config = AgentConfig(**db_config)

    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(agent_config.name)

    # 将agent_config的配置改成请求的用户ID
    agent_config.user_id = login_user.user_id

    # 基于配置创建流式对话智能体实例
    chat_agent = GeneralAgent(agent_config)
    await chat_agent.init_agent()

    # 备份用户原始输入，用于后续数据库存储和记忆检索
    original_user_input = req.user_input

    # 整合用户输入内容，将文本和附件URL合并处理
    req.user_input = build_completion_user_input(
        file_url=req.file_url,
        user_input=req.user_input
    )

    # 构建系统提示词基础指令
    system_prompt = (
        agent_config.system_prompt
        if agent_config.system_prompt.strip()
        else SYSTEM_PROMPT
    )

    # 根据记忆开关选择历史记录获取策略
    if agent_config.enable_memory:
        # 记忆模式：通过向量检索获取语义相关的历史对话
        history = await memory_client.search(
            query=original_user_input,
            run_id=req.dialog_id
        )
        history_text = "\n".join(
            msg.get("memory", "")
            for msg in history.get("results", [])
        )
    else:
        # 普通模式：从数据库按时间顺序获取完整历史
        history_records = await HistoryService.select_history(
            dialog_id=req.dialog_id
        )
        history_text = build_completion_history_messages(history_records)

    # 将历史记录注入系统提示词
    system_prompt = build_completion_system_prompt(system_prompt, history_text)

    # 构建完整消息列表（System → Human 的标准对话结构）
    messages: List[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=req.user_input),
    ]

    # 事件队列：收集工具调用、状态变更等非文本事件
    events = []

    async def general_generate():
        """
        流式响应生成器

        实时处理AI助手的响应流，将内容按SSE格式返回给前端，
        同时收集和处理各种事件（工具调用、心跳等）
        """
        response_content = " "  # 累积完整响应文本，用于后续持久化

        try:
            async for event in chat_agent.astream(messages):
                if event.get("type") == "response_chunk":
                    # 文本片段：按SSE标准格式封装并流式传输
                    yield f'data: {json.dumps(event)}\n\n'
                    response_content += event["data"].get("chunk")
                else:
                    # 其他事件（工具调用、状态更新等）：记录并同步传输
                    events.append(event)
                    yield f'data: {json.dumps(event)}\n\n'
        finally:
            # 无论流式响应是否完整，都要保存对话记录
            if agent_config.enable_memory:
                # 异步保存到记忆系统（不阻塞响应）
                await memory_client.add(
                    messages=[
                        {"role": "user", "content": original_user_input},
                        {"role": "assistant", "content": response_content}
                    ],
                    run_id=req.dialog_id
                )

            # 持久化到MySQL数据库
            await HistoryService.save_chat_history(
                role="assistant",
                content=response_content,
                events=events,
                dialog_id=req.dialog_id,
                memory_enable=agent_config.enable_memory
            )

    # 先保存用户输入到数据库（确保对话完整性）
    await HistoryService.save_chat_history(
        role="user",
        content=original_user_input,
        events=events,
        dialog_id=req.dialog_id,
        memory_enable=agent_config.enable_memory
    )

    # 返回SSE流式响应
    return WatchedStreamingResponse(
        content=general_generate(),
        callback=chat_agent.stop_streaming_callback,
        media_type="text/event-stream"
    )
