import inspect
import json
from typing import List

from langchain_core.messages import ToolCall
from openai.types.chat import ChatCompletionMessageToolCall
from pydantic import create_model
from agentchat.schema.mcp import MCPSSEConfig, MCPWebsocketConfig, MCPStreamableHttpConfig


def convert_langchain_tool_calls(tool_calls: List[ChatCompletionMessageToolCall]):
    if not tool_calls:
        return []

    langchain_tool_calls: List[ToolCall] = []
    for tool_call in tool_calls:
        langchain_tool_calls.append(
            ToolCall(id=tool_call.id, args=json.loads(tool_call.function.arguments), name=tool_call.function.name))

    return langchain_tool_calls

def convert_mcp_config(servers_info: dict | list):

    def convert_single_mcp(server_info):
        if isinstance(server_info, dict):
            if server_info.get("type") == "sse":
                return MCPSSEConfig(
                    url=server_info.get("url"),
                    server_name=server_info.get("server_name")
                )
            elif server_info.get("type") == "websocket":
                return MCPWebsocketConfig(
                    url=server_info.get("url"),
                    server_name=server_info.get("server_name")
                )
            elif server_info.get("type") == "streamable_http":
                return MCPStreamableHttpConfig(
                    url=server_info.get("url"),
                    server_name=server_info.get("server_name")
                )
            else:
                # Stdio
                pass

    if isinstance(servers_info, dict):
        return convert_single_mcp(servers_info)
    else:
        return [convert_single_mcp(server_info) for server_info in servers_info]


def mcp_tool_to_args_schema(name, description, args_schema) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": args_schema
        }
    }

def function_to_args_schema(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown schema annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"schema": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }