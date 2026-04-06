"""
MCP Streamable HTTP / JSON-RPC 端点
核心要点：
1. 所有请求走同一个 POST /{server_key} 端点
2. Session ID 通过 Header Mcp-Session-Id 传递（不走 Query Param）
3. POST 响应格式由客户端 Accept 头决定：
      - application/json        → 直接返回 JSONResponse（单次应答）
      - text/event-stream       → 返回 SSE StreamingResponse（流式应答）
4. GET /{server_key} 维持长连接 SSE 通道，接收服务端主动推送的通知
5. DELETE /{server_key} 关闭 session
"""

import asyncio
import json
import time
from loguru import logger
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from agentchat.mcp_proxy.json_rpc import rpc_error, rpc_ok, check_auth, sse_event, sse_ping, process_jsonrpc
from agentchat.schemas.json_rpc import HealthResponse
from agentchat.mcp_proxy.session.manager import SessionManager
from agentchat.mcp_proxy.session.models import ClientCapabilities, ClientInfo
from agentchat.settings import app_settings

router = APIRouter(prefix="/mcp", tags=["MCP-Streamable-Http"])

# session_id -> asyncio.Queue，用于服务端向 GET SSE 长连接推送通知
_sse_queues: dict[str, asyncio.Queue] = {}


# 依赖函数
def get_session_manager(request: Request) -> SessionManager:
    return request.app.state.session_manager


# POST /{server_key}  ——  主入口，处理所有 JSON-RPC 请求
@router.post("/{server_key}")
async def streamable_http_endpoint(
    server_key: str,
    request: Request,
    sm: SessionManager = Depends(get_session_manager),
):
    """
    Streamable HTTP 主入口。

    流程：
    - initialize：无需 Mcp-Session-Id，服务端创建 session 并在响应 Header 返回
    - 其余方法：必须携带 Mcp-Session-Id Header
    - 响应格式由 Accept Header 决定（json / text/event-stream）
    """
    if not check_auth(request):
        return JSONResponse(
            rpc_error(None, -32001, "Authentication failed").model_dump(),
            status_code=401,
        )

    # 解析请求体
    try:
        payload = json.loads(await request.body())
    except json.JSONDecodeError as e:
        return JSONResponse(
            rpc_error(None, -32700, "Parse error", str(e)).model_dump(),
            status_code=400,
        )

    method = payload.get("method", "")
    params = payload.get("params") or {}
    rpc_id = payload.get("id")
    accept = request.headers.get("Accept", "application/json")

    logger.info(f"Streamable HTTP POST: method={method}, server={server_key}, accept={accept}")

    # initialize：创建 session
    if method == "initialize":
        client_info_raw = params.get("clientInfo", {})
        capabilities_raw = params.get("capabilities", {})

        # 只传入 dataclass 声明过的字段，忽略客户端多传的未知字段（如 sampling）
        import dataclasses
        _ci_fields = {f.name for f in dataclasses.fields(ClientInfo)} if dataclasses.is_dataclass(ClientInfo) else set(vars(ClientInfo()).keys())
        _cap_fields = {f.name for f in dataclasses.fields(ClientCapabilities)} if dataclasses.is_dataclass(ClientCapabilities) else set(vars(ClientCapabilities()).keys())

        session = await sm.create_session(
            server_name=server_key,
            environment="prod",
            client_info=ClientInfo(**{k: v for k, v in client_info_raw.items() if k in _ci_fields}) if isinstance(client_info_raw, dict) else ClientInfo(),
            capabilities=ClientCapabilities(**{k: v for k, v in capabilities_raw.items() if k in _cap_fields}) if isinstance(capabilities_raw, dict) else ClientCapabilities(),
        )

        logger.info(
            f"Session created: {session.session_id}, "
            f"client={client_info_raw.get('name', 'unknown')} v{client_info_raw.get('version', 'unknown')}"
        )

        response_body = rpc_ok(
            rpc_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": app_settings.server_name or "MCP-Proxy",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "tools": {"listChanged": True},
                },
            },
        ).model_dump(exclude_none=True)

        # session ID 通过响应 Header 返回，不放在 body 里
        return JSONResponse(
            content=response_body,
            headers={"Mcp-Session-Id": session.session_id},
        )

    # 非 initialize：必须有 session
    session_id = request.headers.get("Mcp-Session-Id")
    if not session_id:
        return JSONResponse(
            rpc_error(rpc_id, -32000, "Missing session", "Mcp-Session-Id header is required").model_dump(),
            status_code=400,
        )

    session = await sm.get_session(session_id)
    if not session:
        return JSONResponse(
            rpc_error(rpc_id, -32000, "Session not found").model_dump(),
            status_code=404,
        )

    if session.server_name != server_key:
        return JSONResponse(
            rpc_error(rpc_id, -32000, "Session mismatch").model_dump(),
            status_code=400,
        )

    await sm.touch_session(session_id)

    # 根据 Accept 头决定响应方式
    if "text/event-stream" in accept:
        return await _handle_streaming_response(server_key, session_id, payload)
    else:
        return await _handle_json_response(server_key, session_id, payload)


# GET /{server_key}  ——  长连接 SSE 通道，接收服务端主动推送的通知
@router.get("/{server_key}")
async def sse_listen_endpoint(
    server_key: str,
    request: Request,
    sm: SessionManager = Depends(get_session_manager),
):
    """
    客户端建立 SSE 长连接，用于接收服务端主动推送的通知。
    例如：tools/list_changed、resources/updated 等。

    客户端必须先通过 POST initialize 拿到 session ID，再建立此连接。
    """
    if not check_auth(request):
        return Response(content="Authentication failed", status_code=401)

    accept = request.headers.get("Accept", "")
    if "text/event-stream" not in accept:
        return Response(
            content="Accept: text/event-stream is required",
            status_code=406,
        )

    session_id = request.headers.get("Mcp-Session-Id")
    if not session_id:
        return Response(
            content="Mcp-Session-Id header is required",
            status_code=400,
        )

    session = await sm.get_session(session_id)
    if not session:
        return Response(content="Session not found", status_code=404)

    if session.server_name != server_key:
        return Response(content="Session mismatch", status_code=400)

    # 为该 session 创建推送队列
    queue: asyncio.Queue = asyncio.Queue()
    _sse_queues[session_id] = queue

    logger.info(f"SSE listen connected: session={session_id}, server={server_key}")

    async def event_generator() -> AsyncGenerator[bytes, None]:
        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"SSE listen disconnected: session={session_id}")
                    break
                try:
                    item: dict = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield sse_event(item).encode()
                except asyncio.TimeoutError:
                    # 心跳，保持连接
                    yield sse_ping().encode()
        finally:
            _sse_queues.pop(session_id, None)
            logger.info(f"SSE listen cleanup: session={session_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Connection": "keep-alive",
        },
    )


# DELETE /{server_key}  ——  关闭 session
@router.delete("/{server_key}")
async def close_session_endpoint(
    server_key: str,
    request: Request,
    sm: SessionManager = Depends(get_session_manager),
):
    if not check_auth(request):
        return JSONResponse(
            rpc_error(None, -32001, "Authentication failed").model_dump(),
            status_code=401,
        )

    session_id = request.headers.get("Mcp-Session-Id")
    if not session_id:
        return JSONResponse(
            rpc_error(None, -32000, "Missing session", "Mcp-Session-Id header is required").model_dump(),
            status_code=400,
        )

    session = await sm.get_session(session_id)
    if not session:
        return JSONResponse(
            rpc_error(None, -32000, "Session not found").model_dump(),
            status_code=404,
        )

    if session.server_name != server_key:
        return JSONResponse(
            rpc_error(None, -32000, "Session mismatch").model_dump(),
            status_code=400,
        )

    await sm.delete_session(session_id)
    _sse_queues.pop(session_id, None)

    logger.info(f"Session deleted: {session_id}")
    return Response(status_code=200)


# Health
@router.get("/{server_key}/health", response_model=HealthResponse)
async def health_check(server_key: str):
    return HealthResponse(
        status="UP",
        server_name=app_settings.server_name or "MCP-Proxy",
        active_sessions=len(_sse_queues),
        timestamp=int(time.time()),
    )


# 内部：JSON 单次应答
async def _handle_json_response(
    server_key: str,
    session_id: str,
    payload: dict,
) -> JSONResponse:
    """
    客户端 Accept: application/json 时，直接在 HTTP 响应体返回结果。
    notifications/* 类通知无需响应，返回 204。
    """
    response = await process_jsonrpc(server_key, session_id, payload)
    if response is None:
        return Response(status_code=204)

    return JSONResponse(
        content=response.model_dump(exclude_none=True),
        headers={"Mcp-Session-Id": session_id},
    )


# 内部：SSE 流式应答
async def _handle_streaming_response(
    server_key: str,
    session_id: str,
    payload: dict,
) -> StreamingResponse:
    """
    客户端 Accept: text/event-stream 时，以 SSE 格式流式返回结果。
    适用于 tools/call 等可能产生渐进式输出的方法。
    """
    async def generator() -> AsyncGenerator[bytes, None]:
        response = await process_jsonrpc(server_key, session_id, payload)
        if response is not None:
            yield sse_event(response.model_dump(exclude_none=True)).encode()

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Mcp-Session-Id": session_id,
        },
    )


# ---------------------------------------------------------------------------
# 工具函数：服务端主动推送通知（供其他模块调用）
#
# 用法示例：
#   await push_notification(session_id, {
#       "jsonrpc": "2.0",
#       "method": "notifications/tools/list_changed",
#       "params": {}
#   })
# ---------------------------------------------------------------------------

async def push_notification(session_id: str, notification: dict) -> bool:
    """
    向指定 session 的 GET SSE 长连接推送通知。
    返回 True 表示推送成功，False 表示该 session 没有活跃的 SSE 连接。
    """
    queue = _sse_queues.get(session_id)
    if not queue:
        logger.warning(f"No active SSE listener for session={session_id}, notification dropped")
        return False
    await queue.put(notification)
    logger.info(f"Notification pushed to session={session_id}: method={notification.get('method')}")
    return True


async def broadcast_notification(notification: dict) -> int:
    """
    向所有活跃 session 的 SSE 连接广播通知。
    返回成功推送的 session 数量。
    """
    count = 0
    for session_id, queue in list(_sse_queues.items()):
        await queue.put(notification)
        count += 1
    logger.info(f"Notification broadcasted to {count} sessions: method={notification.get('method')}")
    return count
