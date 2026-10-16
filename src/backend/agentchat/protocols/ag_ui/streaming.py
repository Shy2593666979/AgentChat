import json
from uuid import uuid4

import anyio
from ag_ui.core import (
    CustomEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder
from loguru import logger

from agentchat.utils.logging import get_log_context, observe_stream

PROTOCOL = "ag-ui/1.0"


class StreamAdapter:
    """每个请求独立持有运行和消息标识，不共享可变运行状态。"""

    def __init__(self, thread_id=None):
        self.thread_id = thread_id or uuid4().hex
        self.run_id = uuid4().hex
        self.messages = {}
        self.tools = {}
        self.interrupts = []
        self.failed = False

    def custom(self, name, value):
        return CustomEvent(name="agentchat." + name, value=value)

    def text(self, delta, key="answer", metadata=None):
        if not isinstance(delta, str) or not delta:
            return []
        events = []
        if key not in self.messages:
            self.messages[key] = uuid4().hex
            events.append(
                TextMessageStartEvent(
                    message_id=self.messages[key],
                    role="assistant",
                    metadata=metadata,
                )
            )
        events.append(
            TextMessageContentEvent(
                message_id=self.messages[key],
                delta=delta,
                metadata=metadata,
            )
        )
        return events

    def tool(self, identity, name, status, content="", args=None, metadata=None):
        """调用参数结束与工具执行结果分别编码，工具错误不自动终止整轮。"""
        events = []
        if identity not in self.tools:
            self.tools[identity] = name
            events.append(
                ToolCallStartEvent(
                    tool_call_id=identity,
                    tool_call_name=name,
                    metadata=metadata,
                )
            )
            events.append(
                ToolCallArgsEvent(
                    tool_call_id=identity,
                    delta=json.dumps(args or {}, ensure_ascii=False),
                )
            )
            events.append(ToolCallEndEvent(tool_call_id=identity))
        if status in ("END", "ERROR"):
            events.append(
                ToolCallResultEvent(
                    message_id=uuid4().hex,
                    tool_call_id=identity,
                    content=(
                        content
                        if isinstance(content, str)
                        else json.dumps(content, ensure_ascii=False)
                    ),
                    role="tool",
                    metadata={
                        **(metadata or {}),
                        "status": status,
                    },
                )
            )
        return events

    def convert(self, event):
        raise NotImplementedError

    def finish(self):
        events = [TextMessageEndEvent(message_id=value) for value in self.messages.values()]
        outcome = (
            {
                "type": "interrupt",
                "interrupts": self.interrupts,
            }
            if self.interrupts
            else {
                "type": "success",
            }
        )
        events.append(
            RunFinishedEvent(
                thread_id=self.thread_id,
                run_id=self.run_id,
                outcome=outcome,
            )
        )
        return events


def decode_event(value):
    """复用现有生成器，兼容已经编码的单条 SSE 帧。"""
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("data:"):
            value = value[5:].strip()
        if not value or value in ("DONE", "[DONE]"):
            return None
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError("流式事件必须是对象")
    return value


def protocol_stream(source, request, scene, thread_id=None):
    """仅对显式选择 AG-UI 的客户端启用适配，旧客户端保持原协议。"""
    run_id = get_log_context().get("run_id") or uuid4().hex
    if request is None or request.headers.get("x-agentchat-protocol") != PROTOCOL:
        return observe_stream(source, scene=scene, thread_id=thread_id, run_id=run_id)
    from agentchat.protocols.ag_ui.conversation import ConversationAdapter
    from agentchat.protocols.ag_ui.mars import MarsAdapter
    from agentchat.protocols.ag_ui.mcp import McpAdapter
    from agentchat.protocols.ag_ui.workspace import WorkspaceAdapter

    adapter = {
        "conversation": ConversationAdapter,
        "mars": MarsAdapter,
        "workspace": WorkspaceAdapter,
        "mcp": McpAdapter,
    }[scene](thread_id)
    adapter.run_id = run_id
    return observe_stream(encode_stream(source, adapter), scene=scene, thread_id=thread_id, run_id=run_id)


async def encode_stream(source, adapter):
    encoder = EventEncoder()
    try:
        yield encoder.encode(
            RunStartedEvent(
                thread_id=adapter.thread_id,
                run_id=adapter.run_id,
            )
        )
        async for frame in source:
            event = decode_event(frame)
            if event is not None:
                for converted in adapter.convert(event):
                    yield encoder.encode(converted)
                if adapter.failed:
                    return
        for event in adapter.finish():
            yield encoder.encode(event)
    except Exception:
        logger.exception("AG-UI 流式执行失败")
        yield encoder.encode(
            RunErrorEvent(
                message="执行失败，已保留收到的内容，请重试。",
                code="EXECUTION_ERROR",
            )
        )
    finally:
        # 客户端断开也要关闭上游生成器，执行原接口的历史保存和清理。
        with anyio.CancelScope(shield=True):
            await source.aclose()
