"""
上下文处理
"""
from contextvars import ContextVar
from typing import Optional, Union

from agentchat.utils.logging import bind_log_context

# 请求跟踪 ID, 中间件设置,
trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# 唯一ID, 区分与trace_id, trace_id多个系统间复用, unique_id 用于会话消息上下游处理
unique_id: ContextVar[Optional[str]] = ContextVar("unique_id", default=None)

# 唯一用户ID
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# 对话Agent 名称
agent_name: ContextVar[Optional[str]] = ContextVar("agent_name", default=None)

# 当前模型调用所属会话，子智能体与异步标题任务沿用请求上下文。
conversation_id: ContextVar[Optional[str]] = ContextVar("conversation_id", default=None)


def get_conversation_id_context():
    """获取模型调用关联的会话 ID；非会话任务返回空值。"""
    return conversation_id.get()


def set_conversation_id_context(value: Optional[str]):
    """设置会话 ID，使用 ContextVar 隔离并发请求。"""
    conversation_id.set(value)
    bind_log_context(conversation_id=value)

def get_trace_id_context() -> str:
    """
    获取 trace_id
    """
    if (tid := trace_id.get()) is None:
        raise ValueError("trace_id context not initialized")
    return tid


def set_trace_id_context(tid: str):
    """
    设置 trace_id
    """
    trace_id.set(tid)

def get_user_id_context():
    """
    获取 user id
    """
    if uid := user_id.get():
        return uid
    return None

def set_user_id_context(uid: str):
    """
    设置 user id
    """
    user_id.set(uid)
    bind_log_context(user_id=uid)

def get_agent_name_context():
    """
    获取 agent name
    """
    if ag_name := agent_name.get():
        return ag_name
    return "其他"

def set_agent_name_context(ag_name):
    """
    设置 agent name
    """
    agent_name.set(ag_name)
