from typing import List

from fastapi import FastAPI, APIRouter, Body, Depends
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from starlette.responses import StreamingResponse

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.mars import Mars_System_Prompt
from agentchat.services.mars.mars_agent import MarsAgent, MarsConfig
from agentchat.services.mars.mars_tools.autobuild import construct_auto_build_prompt

router = APIRouter()

class MarsExampleEnum:
    Autobuild_Agent = 1
    Deep_Search = 2
    AI_News = 3
    Query_Knowledge = 4

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

    messages: List[BaseMessage] = [SystemMessage(content=Mars_System_Prompt.format(tools_info=str(tools_schema))),
                                   HumanMessage(content=user_input)]

    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/mars/example")
async def chat_mars_example(example_id: int = Body(..., description="例子ID", embed=True),
                            login_user: UserPayload = Depends(get_login_user)):

    mars_config = MarsConfig(user_id=login_user.user_id)
    mars_agent = MarsAgent(mars_config)

    await mars_agent.init_mars_agent()

    user_input = ""
    if example_id == MarsExampleEnum.Autobuild_Agent:
        user_input = "帮我生成一个智能体，它可以给我预报每天的天气情况，名称跟描述的话请你给他起一个吧"
    elif example_id == MarsExampleEnum.AI_News:
        user_input = "请帮我生成一份今天的AI日报，然后总结之后提供给我一个下载链接"
    elif example_id == MarsExampleEnum.Query_Knowledge:
        user_input = "请你帮我查询我所有的知识库，然后告诉我知识库中都是什么信息，最好还有图表展示什么的。"
    elif example_id == MarsExampleEnum.Deep_Search:
        user_input = "使用深度搜索查一下河南大学"

    messages: List[BaseMessage] = [SystemMessage(content=Mars_System_Prompt),
                                   HumanMessage(content=user_input)]

    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")
