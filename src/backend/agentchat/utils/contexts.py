"""
上下文处理
"""
from contextvars import ContextVar
from typing import Optional, Union


# 请求跟踪 ID, 中间件设置,
trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# 唯一ID, 区分与trace_id, trace_id多个系统间复用, unique_id 用于会话消息上下游处理
unique_id: ContextVar[Optional[str]] = ContextVar("unique_id", default=None)

# 唯一用户ID
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# 对话Agent 名称
agent_name: ContextVar[Optional[str]] = ContextVar("agent_name", default=None)

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