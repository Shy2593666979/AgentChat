import asyncio
import logging
from typing import List, Dict, Any

from langchain_core.tools import BaseTool
from agentchat.services.mcp.multi_client import MultiServerMCPClient
from agentchat.schema.mcp import MCPBaseConfig

logger = logging.getLogger(__name__)

HIDE_FIELDS = ["server_name", "personal_config"]

class MCPManager:
    def __init__(self, mcp_configs: List[MCPBaseConfig], timeout=10):

        connection_info = {
            mcp_config.server_name: mcp_config.model_dump(exclude={"server_name", "personal_config"})
            for mcp_config in mcp_configs
        }

        self.multi_server_client = MultiServerMCPClient(connection_info)
        self.mcp_configs = mcp_configs

        self.timeout = timeout


    async def get_mcp_tools(self) -> list[BaseTool]:
        tools = await self.multi_server_client.get_tools()
        return tools

    async def show_mcp_tools(self) -> dict:
        result = {}
        try:
            for mcp_config in self.mcp_configs:
                server_tools = await self.multi_server_client.get_tools(server_name=mcp_config.server_name)
                tool_list = []
                for tool in server_tools:
                    input_schema = tool.args_schema
                    tool_dict = {
                        'name': tool.name,
                        'description': tool.description,
                        'input_schema': input_schema
                    }
                    tool_list.append(tool_dict)
                result[mcp_config.server_name] = tool_list
            return result
        except Exception as err:
            logger.info(f"Error getting MCP service tool list: {err}")
            return {}

    async def call_mcp_tools(self, tools_info: List[Dict[str, Any]]):
        """
        Asynchronously and concurrently call multiple MCP tools
        
        Args:
            tools_info: List of tool names, List of tool parameters, corresponding one-to-one with tool_names
            
        Returns:
            list: List of tool execution results
        """
        # Get tool list
        tools = await self.get_mcp_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        # Async concurrency
        async def execute_tool(tool_name: str, args: Dict[str, Any]):
            # Create async task list
            if tool_name not in tool_dict:
                return f"Tool {tool_name} does not exist"
            
            tool = tool_dict[tool_name]
            try:
                # Create async task
                if asyncio.iscoroutinefunction(tool.coroutine):
                    result = await tool.coroutine(**args)
                else:
                    # Execute all tasks concurrently
                    result = await asyncio.to_thread(tool.coroutine, **args)
                return result
            except Exception as e:
                logger.error(f"Error executing tool: {e}")
                return f"Error executing tool {tool_name}: {e}"

        # Create task list
        tasks = []
        for tool in tools_info:
            tool_name = tool.get("tool_name")
            tool_args = tool.get("tool_args")
            task = execute_tool(tool_name, tool_args)
            tasks.append(task)
        
        # Execute all tasks concurrently
        try:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(tool_results):
                if isinstance(result, Exception):
                    tool_results[i] = f"Error executing tool {tools_info[i].get("tool_name")}: {result}"
                    logger.error(f"Error executing tool {tools_info[i].get("tool_name")}: {result}")
            return tool_results
        except Exception as err:
            logger.error(f"Error calling tools: {err}")
            return []
