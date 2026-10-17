from fastapi import HTTPException

from agentchat.core.models.manager import ModelManager
from agentchat.database.dao.llm import LLMDao


def task_model_id(task):
    """读取最近一轮使用的模型，兼容尚未记录模型的旧会话。"""
    return next((message.get("model_id") for message in reversed(task.messages or []) if message.get("model_id")), None)


def pending_mcp_action(task):
    if not task.messages:
        return None
    for item in reversed(task.messages[-1].get("content", [])):
        if item.get("type") == "interrupt":
            data = item.get("data", {})
            return data if data.get("status") is False else None
    return None


async def resolve_mcp_model(task, user_id, model_id=None, decision=None, interrupt_id=None):
    """校验会话、模型权限与人工确认状态，再创建本次调用的模型。"""
    if not task or str(task.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="无权访问此 MCP 会话")

    saved_id = task_model_id(task)
    pending = pending_mcp_action(task)
    if decision:
        if not pending or decision not in pending.get("allowed_decisions", []):
            raise HTTPException(status_code=409, detail="没有可处理的待确认操作，请刷新会话")
        if interrupt_id is not None and interrupt_id != pending.get("interrupt_id"):
            raise HTTPException(status_code=409, detail="确认操作已过期，请刷新会话")
        if model_id and model_id != saved_id:
            raise HTTPException(status_code=409, detail="等待确认期间不能切换模型")
        selected_id = saved_id
    else:
        if pending:
            raise HTTPException(status_code=409, detail="请先处理待确认操作")
        selected_id = model_id or saved_id

    if not selected_id:
        return None, None

    model = await LLMDao.get_llm_by_id(selected_id)
    if not model:
        raise HTTPException(status_code=404, detail="所选模型不存在")
    if str(model.user_id) not in ("0", str(user_id)):
        raise HTTPException(status_code=403, detail="无权使用所选模型")
    if model.llm_type != "LLM":
        raise HTTPException(status_code=400, detail="MCP 对话仅支持对话模型")

    return selected_id, ModelManager.get_user_model(
        model=model.model, api_key=model.api_key, base_url=model.base_url
    )
