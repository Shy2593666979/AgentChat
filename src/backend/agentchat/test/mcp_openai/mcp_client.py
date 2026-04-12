import json
import logging

from contextlib import AsyncExitStack
from typing import Optional
from mcp.types import Prompt, Tool, Resource, CallToolResult
from mcp import ClientSession, StdioServerParameters, stdio_client


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_path: str, server_env: str):
        command = "python"
        server_params = StdioServerParameters(
            command=command,
            args=[server_path],
            env=json.loads(server_env)
        )

        stdio_transport = await self.exit_stack.enter_async_context((stdio_client(server_params)))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

    async def list_server_tools(self) -> list[Tool]:
        response = await self.session.list_tools()
        tools = response.tools

        return tools

    async def list_server_prompts(self) -> list[Prompt]:
        response = await self.session.list_prompts()
        prompts = response.prompts

        return prompts

    async def list_server_resources(self) -> list[Resource]:
        response = await self.session.list_resources()
        resources = response.resources

        return resources

    async def call_server_tool(self, name, arguments) -> CallToolResult:
        return await self.session.call_tool(name, arguments)

    # @property
    # async def server_info(self):
    #     return await self.session.get_server_info()
