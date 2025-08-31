"""
上下文处理
"""
from contextvars import ContextVar
from typing import Optional, Union


# 请求跟踪 ID, 中间件设置,
trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# 唯一ID, 区分与trace_id, trace_id多个系统间复用, unique_id 用于会话消息上下游处理
unique_id: ContextVar[Optional[str]] = ContextVar("unique_id", default=None)



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

