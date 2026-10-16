from uuid import uuid4

from ag_ui.core import (
    ReasoningEndEvent,
    ReasoningMessageContentEvent,
    ReasoningMessageEndEvent,
    ReasoningMessageStartEvent,
    ReasoningStartEvent,
    RunErrorEvent,
)

from agentchat.protocols.ag_ui.streaming import StreamAdapter


class MarsAdapter(StreamAdapter):
    def __init__(self, thread_id=None):
        super().__init__(thread_id)
        self.reasoning_id = None

    def convert(self, event):
        kind, data = event.get("type"), event.get("data", "")
        attribution = {
            key: event[key]
            for key in ("tool_id", "source", "result_key")
            if event.get(key)
        }
        if kind == "reasoning_chunk":
            events = []
            if not self.reasoning_id:
                self.reasoning_id = uuid4().hex
                events.extend(
                    [
                        ReasoningStartEvent(message_id=self.reasoning_id),
                        ReasoningMessageStartEvent(message_id=self.reasoning_id),
                    ]
                )
            if data:
                events.append(
                    ReasoningMessageContentEvent(
                        message_id=self.reasoning_id,
                        delta=data,
                    )
                )
            return events
        if kind in ("response_chunk", "answer", "answer_chunk", "tool_chunk"):
            text = data if isinstance(data, str) else data.get("chunk", "")
            return self.text(
                text,
                key=event.get("tool_id") or event.get("source") or "answer",
                metadata=attribution,
            )
        if kind in ("tool_start", "tool_end", "tool_error"):
            status = {
                "tool_start": "START",
                "tool_end": "END",
                "tool_error": "ERROR",
            }[kind]
            return self.tool(
                data["id"],
                data.get("name", self.tools.get(data["id"], "tool")),
                status,
                metadata={
                    **data,
                    "status": status,
                },
            )
        if kind == "progress_chunk":
            return [
                self.custom(
                    "mars.progress",
                    {
                        **attribution,
                        "message": data.get("message", ""),
                        "status": data.get("status", "start"),
                        "node": data.get("node", ""),
                    },
                )
            ]
        if kind == "result_start":
            return [self.custom("mars.result_start", attribution)]
        if kind == "error":
            self.failed = True
            return [
                RunErrorEvent(
                    message=data.get("message", "任务失败") if isinstance(data, dict) else data,
                    code="EXECUTION_ERROR",
                )
            ]
        raise ValueError(f"未定义的 Mars 事件：{kind}")

    def finish(self):
        events = []
        if self.reasoning_id:
            events = [
                ReasoningMessageEndEvent(message_id=self.reasoning_id),
                ReasoningEndEvent(message_id=self.reasoning_id),
            ]
        return events + super().finish()
