from typing import List

from fastapi import FastAPI, APIRouter, Body, Depends
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from starlette.responses import StreamingResponse

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.mars import Mars_System_Prompt
from agentchat.services.mars.mars_agent import MarsAgent, MarsConfig
from agentchat.services.mars.mars_tools.autobuild import construct_auto_build_prompt

router = APIRouter()

@router.post("/mars/chat")
async def chat_mars(user_input: str = Body(..., description="用户输入", embed=True),
                    login_user: UserPayload = Depends(get_login_user)):


    mars_config = MarsConfig(user_id=login_user.user_id)
    mars_agent = MarsAgent(mars_config)

    await mars_agent.init_mars_agent()

    tools_schema = []
    for tool in mars_agent.mars_tools:
        if tool.name == "auto_build_agent":
            auto_build_prompt = await construct_auto_build_prompt(mars_config.user_id)
            tool.coroutine.__doc__ = tool.coroutine.__doc__.replace("{{{user_configs_placeholder}}}", auto_build_prompt)
        tools_schema.append(f"工具：{tool.coroutine.__doc__}\n\n")

    messages: List[BaseMessage] = [SystemMessage(content=Mars_System_Prompt.format(tools_info=str(tools_schema))), HumanMessage(content=user_input)]
    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")
