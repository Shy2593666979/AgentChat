import inspect
from pydantic import create_model
from agentchat.schema.mcp import MCPSSEConfig, MCPWebsocketConfig, MCPStreamableHttpConfig


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
    sig = inspect.signature(func)
    fields = {
        name: (param.annotation, ... if param.default is inspect.Parameter.empty else param.default)
        for name, param in sig.parameters.items()
    }
    model = create_model(func.__name__, **fields)
    schema = model.model_json_schema()

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": schema
        },
    }