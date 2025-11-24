from typing import List

from fastapi import FastAPI, APIRouter, Body, Depends
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from starlette.responses import StreamingResponse

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.mars import Mars_System_Prompt
from agentchat.schema.usage_stats import UsageStatsAgentType
from agentchat.services.mars.mars_agent import MarsAgent, MarsConfig
from agentchat.services.mars.mars_tools.autobuild import construct_auto_build_prompt
from agentchat.services.memory.client import memory_client
from agentchat.utils.contexts import set_user_id_context, set_agent_name_context

router = APIRouter(tags=["Mars"])

class MarsExampleEnum:
    Autobuild_Agent = 1
    Deep_Search = 2
    AI_News = 3
    Query_Knowledge = 4

@router.post("/mars/chat")
async def chat_mars(user_input: str = Body(..., description="用户输入", embed=True),
                    login_user: UserPayload = Depends(get_login_user)):
    # 设置全局变量
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.mars_agent)

    mars_config = MarsConfig(user_id=login_user.user_id)
    mars_agent = MarsAgent(mars_config)

    await mars_agent.init_mars_agent()

    memory_messages = await memory_client.search(query=user_input, user_id=login_user.user_id)
    memory_content = str([f"- {msg.get('memory', '')} \n" for msg in memory_messages.get('results', [])])

    messages: List[BaseMessage] = [SystemMessage(content=Mars_System_Prompt.format(memory_content=memory_content)),
                                   HumanMessage(content=user_input)]

    async def general_generate():
        final_response = ""
        async for chunk in mars_agent.ainvoke_stream(messages):
            yield f"data: {chunk}\n\n"
            if chunk.get("type") == "response_chunk":
                final_response += chunk.get("data", "")

        await memory_client.add(user_id=login_user.user_id, messages=[{"role": "user", "content": user_input}, {"role": "assistant", "content": final_response}])

    return StreamingResponse(general_generate(), media_type="text/event-stream")

@router.post("/mars/example")
async def chat_mars_example(example_id: int = Body(..., description="例子ID", embed=True),
                            login_user: UserPayload = Depends(get_login_user)):
    # 设置全局变量
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.mars_agent)

    mars_config = MarsConfig(user_id=login_user.user_id)
    mars_agent = MarsAgent(mars_config)

    await mars_agent.init_mars_agent()

    user_input = ""
    if example_id == MarsExampleEnum.Autobuild_Agent:
        user_input = "帮我生成一个智能体，它可以给我预报每天的天气情况并且可以帮我生成图片，名称跟描述的话请你给他起一个吧，智能体名称字数要处于2-10字之间"
    elif example_id == MarsExampleEnum.AI_News:
        user_input = "请帮我生成一份今天的AI日报，然后总结之后提供给我一个AI日报的图片，不需要详细内容"
    elif example_id == MarsExampleEnum.Query_Knowledge:
        user_input = "请你帮我查询我所有的知识库，然后告诉我知识库中都是什么信息，最好还有图表展示什么的。"
    elif example_id == MarsExampleEnum.Deep_Search:
        user_input = "使用深度搜索查泰山游玩攻略"

    messages: List[BaseMessage] = [SystemMessage(content=Mars_System_Prompt.format(memory_content="")),
                                   HumanMessage(content=user_input)]

    async def general_generate():
        async for chunk in mars_agent.ainvoke_stream(messages):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")
