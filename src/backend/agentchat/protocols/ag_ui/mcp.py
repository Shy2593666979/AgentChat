from uuid import uuid4

from agentchat.protocols.ag_ui.streaming import StreamAdapter


class McpAdapter(StreamAdapter):
    def convert(self, event):
        kind, data = event.get("type"), event.get("event") or {}
        if kind == "text":
            return self.text(event.get("content", ""))
        if kind == "event":
            if data.get("tool_call_id"):
                return self.tool(
                    data["tool_call_id"],
                    data.get("tool_name", "tool"),
                    "ERROR" if data.get("is_error") else data.get("status", "START"),
                    data.get("content", ""),
                    metadata={
                        "title": data.get("title", "执行工具"),
                    },
                )
            return [
                self.custom(
                    "mcp.progress",
                    {
                        "title": data.get("title", "执行工具"),
                        "status": data.get("status", "START"),
                        "is_error": bool(data.get("is_error")),
                        "content": data.get("content", ""),
                    },
                )
            ]
        if kind == "interrupt":
            self.interrupts.append(
                {
                    "id": data.get("interrupt_id") or uuid4().hex,
                    "reason": "confirmation",
                    "message": "请确认 MCP 服务注册操作",
                    "metadata": {
                        "action_requests": data.get("action_requests", []),
                        "review_configs": data.get("review_configs", []),
                        "preview": data.get("preview", []),
                        "allowed_decisions": data.get("allowed_decisions", []),
                        "status": False,
                    },
                }
            )
            return []
        raise ValueError(f"未定义的 MCP 事件：{kind}")
