from ag_ui.core import RunErrorEvent

from agentchat.protocols.ag_ui.streaming import StreamAdapter


class ConversationAdapter(StreamAdapter):
    def convert(self, event):
        kind, data = event.get("type"), event.get("data") or {}
        if kind == "response_chunk":
            return self.text(data.get("chunk", ""))
        if kind in ("agent", "knowledge"):
            return [self.custom(kind, data)]
        if kind == "error":
            self.failed = True
            return [
                RunErrorEvent(
                    message=data.get("message", "执行失败"),
                    code="EXECUTION_ERROR",
                )
            ]
        if kind == "event":
            identity = data.get("tool_call_id")
            if identity:
                return self.tool(
                    identity,
                    data.get("tool_name", "tool"),
                    data.get("status"),
                    data.get("message", ""),
                    data.get("args"),
                    {
                        "title": data.get("title", "执行工具"),
                    },
                )
            return [
                self.custom(
                    "notice",
                    {
                        "title": data.get("title", "提示"),
                        "status": data.get("status", "INFO"),
                        "message": data.get("message", ""),
                    },
                )
            ]
        if kind == "heartbeat":
            return []
        raise ValueError(f"未定义的会话事件：{kind}")
