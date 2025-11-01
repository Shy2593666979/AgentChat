import json

from util import function_to_args_schema
from tavily import TavilyClient
from openai import OpenAI, AsyncOpenAI

tavily_client = TavilyClient("tvly-dev-****************")


class SearchAgent:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="sk-fc40dd0604f04142************"
        )

    async def asteam(self, query):
        tool = function_to_args_schema(self._exec_search_tool)

        messages = [
            {"role": "system", "content": "You are a helpful assistant!"},
            {"role": "user", "content": query}
        ]

        response = await self.client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            tools=[tool]
        )

        if tool_calls := response.choices[0].message.tool_calls:
            for tool_call in tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": None,  # 工具调用结果不需要content，用tool_calls关联
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = await self._exec_search_tool(**tool_args)  # （简省写）因为只要一个工具，所以只要走function call，就定是这个

                messages.append({
                    "role": "tool",
                    "content": tool_result,
                    "tool_call_id": tool_call.id  # 关联到对应的工具调用ID
                })


        response = await self.client.chat.completions.create(
            model="qwen-plus",
            stream=True,
            messages=messages)
        async for chunk in response:
            yield {"content": str(chunk.choices[0].delta.content), "done": True}

        yield {"content": "", "done": False}

    async def _exec_search_tool(self, query: str, max_results: int = 10):
        """根据用户的问题来联网搜索"""
        response = tavily_client.search(
            query=query,
            country="china",
            max_results=max_results
        )

        return "\n\n".join([f'网址:{result["url"]}, 内容: {result["content"]}' for result in response["results"]])
