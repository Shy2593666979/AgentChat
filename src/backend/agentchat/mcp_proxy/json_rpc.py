"""
MCP API 通用工具函数
提供认证、JSON-RPC 响应构建、SSE 格式化、请求处理等共享功能
"""
import json
import time
from typing import Any

from fastapi import Request
from loguru import logger

from agentchat.schemas.json_rpc import JsonRpcError, JsonRpcResponse
from agentchat.mcp_proxy.register_mcp import RegisterMcpService
from agentchat.settings import app_settings


def check_auth(request: Request) -> bool:
    """
    验证请求的认证信息
    支持 Query token 和 Bearer token 两种方式

    Args:
        request: FastAPI Request 对象

    Returns:
        认证成功或已禁用返回 True，否则返回 False
    """
    # 移动到agentchat平台后全部不走鉴权
    return True


    # if not settings.auth_enabled:
    #     return True
    # token = settings.auth_token
    # if not token:
    #     return False
    # if request.query_params.get("token") == token:
    #     return True
    # bearer = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    # return bearer == token


def rpc_ok(rpc_id: Any, result: Any) -> JsonRpcResponse:
    """
    构建成功的 JSON-RPC 响应

    Args:
        rpc_id: JSON-RPC 请求 ID
        result: 返回的结果数据

    Returns:
        JsonRpcResponse 对象
    """
    return JsonRpcResponse(id=rpc_id, result=result)


def rpc_error(
    rpc_id: Any,
    code: int,
    message: str,
    data: str | None = None,
) -> JsonRpcResponse:
    """
    构建错误的 JSON-RPC 响应

    Args:
        rpc_id: JSON-RPC 请求 ID
        code: 错误码
        message: 错误消息
        data: 可选的额外错误数据

    Returns:
        JsonRpcResponse 对象
    """
    return JsonRpcResponse(
        id=rpc_id,
        error=JsonRpcError(code=code, message=message, data=data),
    )


def sse_event(data: dict) -> str:
    """
    将字典序列化为标准 SSE 格式文本

    Args:
        data: 要序列化的字典

    Returns:
        SSE 格式的字符串
    """
    return f"event: message\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_ping() -> str:
    """
    生成 SSE ping 事件

    Returns:
        SSE 格式的 ping 字符串，包含当前时间戳
    """
    return f"event: ping\ndata: {json.dumps({'timestamp': int(time.time() * 1000)})}\n\n"


def handle_initialize(rpc_id: Any, params: dict) -> JsonRpcResponse:
    """
    处理 initialize 方法

    Args:
        rpc_id: JSON-RPC 请求 ID
        params: 初始化参数

    Returns:
        JsonRpcResponse 对象
    """
    client_name = params.get("clientInfo", {}).get("name", "unknown")
    client_version = params.get("clientInfo", {}).get("version", "unknown")
    logger.info(f"Client initializing: {client_name} v{client_version}")
    return rpc_ok(
        rpc_id,
        {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": app_settings.server.name, "version": "1.0.0"},
            "capabilities": {"tools": {"listChanged": True}},
        },
    )


async def handle_tools_list(server_key: str, rpc_id: Any) -> JsonRpcResponse:
    """
    处理 tools/list 方法

    Args:
        server_key: 服务器标识
        rpc_id: JSON-RPC 请求 ID

    Returns:
        JsonRpcResponse 对象
    """
    try:
        tools = await RegisterMcpService.get_tools_for_server(server_key)
        return rpc_ok(rpc_id, {"tools": tools})
    except Exception as e:
        logger.error(f"tools/list failed: {e}")
        return rpc_error(rpc_id, -32603, "Internal error", str(e))


async def handle_tools_call(server_key: str, rpc_id: Any, params: dict) -> JsonRpcResponse:
    """
    处理 tools/call 方法

    Args:
        server_key: 服务器标识
        rpc_id: JSON-RPC 请求 ID
        params: 调用参数

    Returns:
        JsonRpcResponse 对象
    """
    tool_name = params.get("name")
    if not tool_name:
        return rpc_error(rpc_id, -32602, "Invalid params", "name is required")
    try:
        result = await RegisterMcpService.call_tool(
            server_key,
            tool_name,
            params.get("arguments", {}),
        )
        return rpc_ok(rpc_id, result)
    except Exception as e:
        logger.exception(f"tools/call failed: {e}")
        return rpc_error(rpc_id, -32603, "Internal error", str(e))


async def process_jsonrpc(
    server_key: str,
    session_id: str,
    payload: dict,
) -> JsonRpcResponse | None:
    """
    处理 JSON-RPC 请求，路由到对应的处理方法

    Args:
        server_key: 服务器标识
        session_id: 会话 ID
        payload: JSON-RPC 请求体

    Returns:
        JsonRpcResponse 对象，或 None（对于通知类请求）
    """
    method = payload.get("method", "")
    params = payload.get("params") or {}
    rpc_id = payload.get("id")

    logger.info(f"JSON-RPC method={method} server={server_key} session={session_id}")

    if method == "initialize":
        return handle_initialize(rpc_id, params)
    elif method == "tools/list":
        return await handle_tools_list(server_key, rpc_id)
    elif method == "tools/call":
        return await handle_tools_call(server_key, rpc_id, params)
    elif method == "ping":
        return rpc_ok(rpc_id, {})
    elif method == "notifications/initialized":
        logger.info(f"Client initialized: session={session_id}")
        return None
    else:
        return rpc_error(rpc_id, -32601, "Method not found", method)
