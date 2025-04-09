import logging
from typing import Union

from anthropic import Anthropic, AsyncAnthropic
from openai import AsyncOpenAI, OpenAI
from services.mcp.mcp_client import MCPClient

class MCPManager:
    def __init__(self, client: Union[AsyncOpenAI, OpenAI, Anthropic, AsyncAnthropic]):
        self.mcp_server_stack: list[str] = []
        self.chat_client = client
        self.mcp_clients: list[MCPClient] = []
        self.server_client_dict: dict[str, MCPClient] = {}

    # 增加MCP Server的地址
    async def enter_mcp_server(self, server_path):
        self.mcp_server_stack.append(server_path)
        mcp_client = MCPClient()
        # self.mcp_clients.append(mcp_client)
        self.server_client_dict[server_path] = mcp_client

    async def connect_client(self):
        for mcp_server in self.mcp_server_stack:
            mcp_client = self.server_client_dict.get(mcp_server)
            await mcp_client.connect_to_server(mcp_server)
            self.mcp_clients.append(mcp_client)

    async def list_all_server_tools(self):
        """收集所有 MCP 服务器的可用工具

        Returns:
            list: 所有服务器工具的聚合列表，每个工具包含：
                - name (str)
                - description (str)
                - input_schema (dict)
        """
        available_tools = []
        for client in self.mcp_clients:
            available_tools += await client.list_server_tools()
        return available_tools

    async def _chat_model(self, messages, available_tools):
        """根据客户端类型调用对应的聊天模型接口

        Args:
            messages (list): 符合模型规范的对话消息列表
            available_tools (list): 可用的工具列表（用于工具调用）

        Returns:
            dict: 模型返回的响应数据

        Raises:
            NotImplementedError: 当使用未实现的客户端类型时
            ValueError: 当客户端类型不受支持时
            Exception: 其他未知错误

        Supported Clients:
            - AsyncAnthropic: 异步 Claude 模型调用
            - Anthropic: 同步 Claude 模型调用
            - AsyncOpenAI/OpenAI: 当前未实现（抛出异常）
        """
        try:
            match self.chat_client:
                case AsyncAnthropic():
                    response = await self.chat_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=messages,
                        tools=available_tools
                    )
                    return response
                case Anthropic():
                    response = self.chat_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=messages,
                        tools=available_tools
                    )
                    return response
                case AsyncOpenAI():
                    # 暂时不实现
                    raise NotImplementedError("AsyncOpenAI is not implemented yet")
                case OpenAI():
                    # 暂时不实现
                    raise NotImplementedError("OpenAI is not implemented yet")
                case _:
                    raise ValueError("Now MCP Server support OpenAI and Anthropic")

        except Exception as err:
            logging.info(f"chat model appear error: {err}")
            raise

    async def process_query(self, query: str):
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        response = await self.list_all_server_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        response = await self._chat_model(messages, available_tools)

        # Process response and handle tool calls
        final_text = []

        assistant_message_content = []
        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                assistant_message_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
                        }
                    ]
                })

                # Get next response from Claude
                response = await self._chat_model(messages, available_tools)

                final_text.append(response.content[0].text)

        return "\n".join(final_text)
