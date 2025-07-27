from typing import List

from fastapi import FastAPI, APIRouter, Body, Depends
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from starlette.responses import StreamingResponse

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.chat_prompt import SYSTEM_PROMPT
from agentchat.services.mars.mars_agent import MarsAgent, MarsConfig

router = APIRouter()

@router.post("/mars/chat")
async def chat_mars(user_input: str = Body(..., description="用户输入", embed=True),
                    login_user: UserPayload = Depends(get_login_user)):


    mars_config = MarsConfig(user_id=login_user.user_id)
    mars_agent = MarsAgent(mars_config)

    await mars_agent.init_mars_agent()

    messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_input)]
    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")
