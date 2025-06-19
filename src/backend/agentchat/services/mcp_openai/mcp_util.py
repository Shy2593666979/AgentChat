import functools
import json
import logging
from typing import Any

from agentchat.services.mcp_openai.mcp_client import MCPClient
from agentchat.services.mcp_openai.schema import FunctionTool
from mcp.types import Tool as MCPTool

from agentchat.services.mcp_openai.strict_schema import ensure_strict_json_schema


class MCPUtil:
    """Set of utilities for interop between MCP and Agents SDK tools."""

    @classmethod
    async def get_all_function_tools(
        cls, clients: list[MCPClient], convert_schemas_to_strict: bool=True
    ) -> list[FunctionTool]:
        """Get all function tools from a list of MCP servers."""
        tools = []
        tool_names: set[str] = set()
        for client in clients:
            server_tools = await cls.get_function_tools(client, convert_schemas_to_strict)
            server_tool_names = {tool.name for tool in server_tools}
            if len(server_tool_names & tool_names) > 0:
                raise ValueError(
                    f"Duplicate tool names found across MCP servers: "
                    f"{server_tool_names & tool_names}"
                )
            tool_names.update(server_tool_names)
            tools.extend(server_tools)

        return tools

    @classmethod
    async def get_function_tools(cls, client: MCPClient, convert_schemas_to_strict: bool) -> list[FunctionTool]:
        """Get all function tools from a single MCP server."""

        tools = await client.list_server_tools()

        return [cls.to_function_tool(tool, client, convert_schemas_to_strict) for tool in tools]

    @classmethod
    def to_function_tool(cls, tool: MCPTool, client: MCPClient, convert_schemas_to_strict: bool) -> FunctionTool:
        """Convert an MCP tool to an Agents SDK function tool."""
        invoke_func = functools.partial(cls.run_mcp_tool, client, tool)
        schema, is_strict = tool.inputSchema, False

        # MCP spec doesn't require the inputSchema to have `properties`, but OpenAI spec does.
        if "properties" not in schema:
            schema["properties"] = {}

        if convert_schemas_to_strict:
            try:
                schema = ensure_strict_json_schema(schema)
                is_strict = True
            except Exception as e:
                logging.info(f"Error converting MCP schema to strict mode: {e}")

        return FunctionTool(
            name=tool.name,
            description=tool.description or "",
            params_json_schema=schema,
            on_run_tool=invoke_func,
            strict_json_schema=is_strict,
        )
    
    @classmethod
    async def run_mcp_tool(
        cls, client: MCPClient, tool: MCPTool, input_json: str
    ) -> str:
        """Invoke an MCP tool and return the result as a string."""
        try:
            json_data: dict[str, Any] = json.loads(input_json) if input_json else {}
        except Exception as e:
            logging.debug(f"Invalid JSON input for tool {tool.name}: {input_json}")
            raise ValueError(
                f"Invalid JSON input for tool {tool.name}: {input_json}"
            ) from e

        logging.debug(f"Invoking MCP tool {tool.name} with input {input_json}")

        try:
            result = await client.call_server_tool(tool.name, json_data)
        except Exception as e:
            logging.error(f"Error invoking MCP tool {tool.name}: {e}")
            raise ValueError(f"Error invoking MCP tool {tool.name}: {e}") from e


        logging.debug(f"MCP tool {tool.name} returned {result}")

        # The MCP tool result is a list of content items, whereas OpenAI tool outputs are a single
        # string. We'll try to convert.
        if len(result.content) == 1:
            tool_output = result.content[0].model_dump_json()
        elif len(result.content) > 1:
            tool_output = json.dumps([item.model_dump() for item in result.content])
        else:
            logging.error(f"Error MCP tool result: {result}")
            tool_output = "Error running tool."

        return tool_output


