"""按完整 ASGI 请求生命周期记录日志，覆盖流式结束与客户端断开。"""

import asyncio
import re
from time import monotonic
from uuid import uuid4

from fastapi.responses import JSONResponse
from loguru import logger

from agentchat.utils import contexts
from agentchat.utils.logging import log_context, log_event


class TraceIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        candidate = headers.get(
            b"x-trace-id", headers.get(b"x-b3-traceid", b"")
        ).decode("latin1")
        trace_id = (
            candidate
            if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", candidate)
            else uuid4().hex
        )
        run_id = uuid4().hex
        state = scope.setdefault("state", {})
        state["trace_id"], state["run_id"] = trace_id, run_id
        started = monotonic()
        status = 500
        response_started = False
        completed = False
        disconnected = False
        raised = False
        context_tokens = [
            (variable, variable.set(None))
            for variable in (
                contexts.trace_id,
                contexts.user_id,
                contexts.conversation_id,
                contexts.agent_name,
            )
        ]
        contexts.set_trace_id_context(trace_id)

        async def receive_request():
            nonlocal disconnected
            message = await receive()
            if message["type"] == "http.disconnect":
                disconnected = True
            return message

        async def send_response(message):
            nonlocal status, response_started, completed, disconnected
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                message = {
                    **message,
                    "headers": [
                        (key, value)
                        for key, value in message.get("headers", [])
                        if key.lower() != b"x-trace-id"
                    ]
                    + [(b"x-trace-id", trace_id.encode())],
                }
            try:
                await send(message)
            except OSError:
                disconnected = True
                raise
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                completed = True

        with log_context(inherit=False, trace_id=trace_id, run_id=run_id):
            log_event(
                "api.request", "请求开始", method=scope["method"], path=scope["path"]
            )
            try:
                await self.app(scope, receive_request, send_response)
            except asyncio.CancelledError:
                disconnected = True
                raise
            except Exception:
                if disconnected:
                    raise
                raised = True
                logger.bind(component="api.request").exception("请求处理异常")
                if response_started:
                    raise
                response = JSONResponse(
                    status_code=500,
                    content={
                        "code": -1,
                        "error_msg": "10500: 系统错误，请重试",
                    },
                )
                await response(scope, receive_request, send_response)
            finally:
                outcome = (
                    "请求失败"
                    if raised or (completed and status >= 500)
                    else "请求完成" if completed else "请求取消"
                )
                if disconnected and not completed:
                    outcome = "请求取消"
                log_event(
                    "api.request",
                    outcome,
                    level="ERROR" if outcome == "请求失败" else "INFO",
                    method=scope["method"],
                    path=scope["path"],
                    status=status,
                    duration_ms=round((monotonic() - started) * 1000),
                )
                for variable, token in reversed(context_tokens):
                    variable.reset(token)
