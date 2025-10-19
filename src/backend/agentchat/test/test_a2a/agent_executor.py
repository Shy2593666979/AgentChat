from uuid import uuid4

from a2a.utils import new_text_artifact

from agent import SearchAgent
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.types import TaskArtifactUpdateEvent
from a2a.server.events import EventQueue


class SearchAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = SearchAgent()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()

        async for chunk in self.agent.asteam(query):
            if chunk["done"]:
                await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                    context_id=context.context_id,
                    task_id=context.task_id,
                    artifact=new_text_artifact(
                        name="current_data",
                        text=chunk["content"]
                    )
                ))


