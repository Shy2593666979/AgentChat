from ag_ui.core import StateSnapshotEvent, StepFinishedEvent, StepStartedEvent

from agentchat.protocols.ag_ui.streaming import StreamAdapter


class WorkspaceAdapter(StreamAdapter):
    def convert(self, event):
        kind, data = event.get("event"), event.get("data") or {}
        if kind in ("task_result", "generate_guide_prompt"):
            return self.text(data.get("chunk", data.get("message", "")))
        if kind == "generate_tasks":
            return [
                StateSnapshotEvent(
                    snapshot={
                        "graph": data.get("graph", []),
                        "tasks": data.get("tasks", []),
                    },
                )
            ]
        if kind == "step_result":
            name = data.get("title", "执行步骤")
            return [
                self.custom(
                    "workspace.step_result",
                    {
                        "title": name,
                        "message": data.get("message", ""),
                    },
                ),
                StepFinishedEvent(step_name=name),
            ]
        if kind == "step_start":
            return [StepStartedEvent(step_name=data.get("title", "执行步骤"))]
        raise ValueError(f"未定义的工作区事件：{kind}")
