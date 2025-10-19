import uuid

import httpx
import uvicorn
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.request_handlers import DefaultRequestHandler
from agent_executor import SearchAgentExecutor
from a2a.server.apps import A2AStarletteApplication

if __name__ == "__main__":

    agent_card = AgentCard(
        name="web_search",
        description="a web search agent",
        url="http://localhost:9999/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[AgentSkill(
            id=str(uuid.uuid4()),
            name="web search",
            description="web search",
            tags=["agent", "web search"]
        )],
        capabilities=AgentCapabilities(streaming=True)
    )

    request_handler = DefaultRequestHandler(
        agent_executor=SearchAgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    uvicorn.run(app.build(), host="0.0.0.0", port=9999)
