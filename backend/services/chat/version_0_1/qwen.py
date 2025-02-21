# -------------------------------
# 该文件目前版本已弃用
# -------------------------------
from typing import List

from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from api.services.tool import ToolService
from prompts.llm_prompt import react_prompt_zh
from tools import action_React

llm = ChatOpenAI()

async def react_chat(query: str, tool_id: List[str] = None):
    tools = []
    tools_name = ToolService.get_tool_name_by_id(tool_id=tool_id)
    for name in tools_name:
        tools.append(action_React[name])
    # for key, tool_model in action_React:
    #     if key in tools_name:
    #         tools.append(tool_model())

    agent = create_structured_chat_agent(llm, tools, react_prompt_zh)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    async for chunk in agent_executor.astream({'input': query}):
        yield chunk.json(ensure_ascii=False)
