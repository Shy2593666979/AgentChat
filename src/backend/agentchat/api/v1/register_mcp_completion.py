"""
接口层：在原有 /completion 基础上新增两个 HITL resume 接口。

新增接口：
  POST /completion/hitl/approve  → 用户同意注册
  POST /completion/hitl/reject   → 用户取消 或 用户提供自然语言修改意见
"""
import json
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agentchat.api.responses.streaming import WatchedStreamingResponse
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.mcp_proxy.agent import abstract_mcp_agent
from agentchat.database.dao.register_task import RegisterMcpTaskDao
from agentchat.utils.contexts import set_user_id_context

router = APIRouter(prefix="/mcp/register", tags=["Completion"])


class CompletionReq(BaseModel):
    query: str
    task_id: str


class HitlApproveReq(BaseModel):
    task_id: str  # 同时作为 thread_id 使用


class HitlRejectReq(BaseModel):
    task_id: str
    # feedback 为空字符串或 None → 纯取消
    # feedback 有内容 → 用户提供了修改意见，触发 revise 循环
    feedback: str = ""


def _extract_text_from_content(content_array):
    """从 content 数组中提取所有文本内容"""
    if not content_array:
        return ""
    return "".join([
        item.get("data", "")
        for item in content_array
        if item.get("type") == "text"
    ])


def _make_sse(event: dict | str) -> str:
    if isinstance(event, str):
        return f'data: {event}'
    return f'data: {json.dumps(event, ensure_ascii=False)}\n\n'


@router.post("/completion")
async def completion(
    req: CompletionReq,
    login_user: UserPayload = Depends(get_login_user)
):
    set_user_id_context(login_user.user_id)

    await RegisterMcpTaskDao.create_task_if_not_exists(req.task_id, login_user.user_id)
    current_task = await RegisterMcpTaskDao.get_task(req.task_id)

    if current_task.messages:
        history_context = "\n可供参考的历史消息： " + "\n".join([
            f"query: {msg['query']} \n answer: {_extract_text_from_content(msg.get('content', []))}"
            for msg in current_task.messages
        ])
        processed_query = req.query + history_context
    else:
        processed_query = req.query

    content_array = []

    async def general_generate():
        try:
            async for event in abstract_mcp_agent.astream(
                [HumanMessage(processed_query)],
                thread_id=req.task_id,   # ← 用 task_id 作为 thread_id
            ):
                _collect_and_yield(event, content_array)
                yield _make_sse(event)
        finally:
            await RegisterMcpTaskDao.add_task_message(
                task_id=req.task_id,
                message={"query": req.query, "content": content_array}
            )

    return WatchedStreamingResponse(
        content=general_generate(),
        media_type="text/event-stream",
    )


@router.post("/completion/hitl/approve")
async def hitl_approve(
    req: HitlApproveReq,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    用户同意注册 MCP Server。
    构建 approve Command，resume Agent 继续执行注册。
    """
    set_user_id_context(login_user.user_id)


    command = Command(
        resume={
            "decisions": [{"type": "approve"}]
        }
    )

    await RegisterMcpTaskDao.update_message_interrupt_status(req.task_id)

    content_array = []

    async def approve_generate():
        try:
            async for event in abstract_mcp_agent.astream_resume(command, thread_id=req.task_id):
                _collect_and_yield(event, content_array)
                yield _make_sse(event)
        finally:
            yield _make_sse("DONE")
            await RegisterMcpTaskDao.extend_previous_content_messages(req.task_id, content_array)
            # await RegisterMcpTaskDao.add_task_message(
            #     task_id=req.task_id,
            #     message={"query": "[HITL:approve]", "content": content_array}
            # )

    return WatchedStreamingResponse(
        content=approve_generate(),
        media_type="text/event-stream",
    )


@router.post("/completion/hitl/reject")
async def hitl_reject(
    req: HitlRejectReq,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    用户拒绝注册，分两种情况：

    情况 1：feedback 为空 → 纯取消
      → reject 不带 message，Agent 收到后告知用户已取消，流程结束

    情况 2：feedback 有内容 → 自然语言修改意见
      → reject 带 message（即用户反馈），HITL middleware 将 message 注入对话
      → Agent 根据 System Prompt 自动调用：
          revise_mcp_json(mcp_json_str, feedback)
          → verify_mcp_json
          → register_mcp_server（再次触发 HITL 中断，进入下一轮确认）

    核心机制：
        HumanInTheLoopMiddleware 的 reject decision 会把 message 作为
        ToolMessage 内容注入到对话历史中，Agent 读到后按 System Prompt 指引
        自动触发 revise 循环，无需任何额外 hack。
    """
    set_user_id_context(login_user.user_id)

    feedback = req.feedback.strip()

    if feedback:
        # 有修改意见 → reject + message（触发 revise 循环）
        command = Command(
            resume={
                "decisions": [
                    {
                        "type": "reject",
                        "message": feedback,
                    }
                ]
            }
        )
    else:
        # 纯取消 → reject 不带 message
        command = Command(
            resume={
                "decisions": [{"type": "reject"}]
            }
        )

    await RegisterMcpTaskDao.update_message_interrupt_status(req.task_id)

    content_array = []
    log_query = f"[HITL:reject] feedback={feedback or '(取消)'}"

    async def reject_generate():
        try:
            async for event in abstract_mcp_agent.astream_resume(command, thread_id=req.task_id):
                _collect_and_yield(event, content_array)
                yield _make_sse(event)
        finally:
            yield _make_sse("DONE")
            await RegisterMcpTaskDao.extend_previous_content_messages(req.task_id, content_array)
            # await RegisterMcpTaskDao.add_task_message(
            #     task_id=req.task_id,
            #     message={"query": log_query, "content": content_array}
            # )

    return WatchedStreamingResponse(
        content=reject_generate(),
        media_type="text/event-stream",
    )


def _collect_and_yield(event: dict, content_array: list):
    """收集事件到 content_array，与原有逻辑保持一致"""
    if event.get("type") == "text":
        content_array.append({"type": "text", "data": event.get("content", "")})
    elif event.get("type") == "interrupt":
        content_array.append({"type": "interrupt", "data": event.get("event", {})})
    else:
        content_array.append({"type": "event", "data": event.get("event", {})})