"""验证统一日志、脱敏、轮转、并发上下文与流式请求生命周期。"""

import asyncio
import json
import logging

import httpx
import pytest
from agentchat.middleware.trace_id_middleware import TraceIDMiddleware
from agentchat.protocols.ag_ui.streaming import protocol_stream
from agentchat.utils.contexts import set_conversation_id_context, set_user_id_context
from agentchat.utils.logging import (
    configure_logging,
    get_log_context,
    log_context,
    log_event,
    observe_stream,
    record_model_usage,
    register_log_secrets,
    tool_operation,
)
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from loguru import logger


@pytest.fixture
def logs(tmp_path):
    configure_logging(
        directory=tmp_path,
        console=False,
        secrets={
            "api_key": "private-provider-key",
            "password": "private-db-password",
        },
    )

    def read(filename="app.log"):
        logger.complete()
        return (tmp_path / filename).read_text(encoding="utf-8")

    yield read
    logger.complete()
    logger.remove()


def test_unified_outputs_redact_secrets_and_keep_safe_traceback(logs):
    register_log_secrets("runtime-private-model-key")
    with log_context(trace_id="trace-safe", user_id="3", run_id="run-safe"):
        log_event("model", "配置失败", level="ERROR", api_key="other-private-key")
        logging.getLogger("database").warning("password=private-db-password")
        logging.getLogger("database").warning("多行告警\n告警详情")
        logger.info(
            "Bearer eyJabc.abcdef.abcdef api_key=private-provider-key https://user:password@example.test/path?token=secret"
        )
        logger.debug("不应记录的完整聊天内容")
        logger.error(
            "runtime-private-model-key mysql+pymysql://dbuser:dbpass@example.test/db?token=secret"
        )
        logger.error(
            "SQL failed\n[parameters: ('private-chat-body',)]\n(Background on this error)"
        )
        try:
            hidden_local = "private-provider-key"
            raise ValueError("api_key=" + hidden_local)
        except ValueError:
            logger.exception("模型执行失败")
    text = logs()
    assert "trace_id=trace-safe" in text
    assert "user_id=3" in text
    assert "database" in text and "WARNING" in text
    warning_header = next(line for line in text.splitlines() if "多行告警" in line)
    assert "run_id=run-safe" in warning_header
    assert "Traceback" in text and "ValueError" in text
    assert "[REDACTED]" in text
    for secret in (
        "private-provider-key",
        "private-db-password",
        "other-private-key",
        "eyJabc",
        "user:password",
        "?token",
        "不应记录的完整聊天内容",
        "runtime-private-model-key",
        "dbuser",
        "dbpass",
        "private-chat-body",
    ):
        assert secret not in text
    errors = logs("error.log")
    assert "模型执行失败" in errors and "database" not in errors
    assert "\x1b[" not in text


def test_http_logs_cover_full_stream_and_isolate_parallel_requests(logs):
    app = FastAPI()
    app.add_middleware(TraceIDMiddleware)

    @app.get("/stream/{identity}")
    async def stream(identity: str):
        set_user_id_context(identity)
        set_conversation_id_context("conversation-" + identity)

        async def generate():
            yield b"first"
            await asyncio.sleep(0.02)
            await asyncio.to_thread(record_model_usage, "test-model", int(identity), 2)
            log_event("test", "业务流结束")
            yield b"last"

        return StreamingResponse(generate())

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            responses = await asyncio.gather(
                *(
                    client.get(
                        "/stream/" + identity,
                        headers={
                            "X-Trace-ID": "trace-" + identity,
                        },
                    )
                    for identity in ("1", "2")
                )
            )
        assert all(response.text == "firstlast" for response in responses)
        assert [response.headers["x-trace-id"] for response in responses] == [
            "trace-1",
            "trace-2",
        ]
        assert get_log_context() == {}

    asyncio.run(check())
    text = logs()
    for identity, other in (("1", "2"), ("2", "1")):
        lines = [
            line for line in text.splitlines() if "trace_id=trace-" + identity in line
        ]
        assert any("业务流结束" in line for line in lines)
        assert lines[-1].find("请求完成") >= 0
        assert "conversation_id=conversation-" + identity in lines[-1]
        assert not any(
            "conversation_id=conversation-" + other in line for line in lines
        )
        assert any("input_tokens=" + identity in line for line in lines)


@pytest.mark.parametrize("error_type", [RuntimeError, OSError])
def test_http_error_has_trace_header_and_safe_response(logs, error_type):
    app = FastAPI()
    app.add_middleware(TraceIDMiddleware)

    @app.get("/failure")
    async def failure():
        raise error_type("api_key=private-provider-key")

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/failure")
        assert response.status_code == 500
        assert response.headers["x-trace-id"]
        assert "private-provider-key" not in response.text

    asyncio.run(check())
    assert "请求失败" in logs()
    assert "private-provider-key" not in logs()


def test_network_disconnect_is_cancelled_without_sending_new_response(logs):
    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"first",
                "more_body": True,
            }
        )

    async def send(message):
        if message["type"] == "http.response.body":
            raise OSError("connection closed")

    async def receive():
        return {
            "type": "http.request",
            "body": b"",
        }

    async def check():
        with log_context(user_id="previous-request"):
            with pytest.raises(OSError):
                await TraceIDMiddleware(app)(
                    {
                        "type": "http",
                        "method": "POST",
                        "path": "/stream",
                    },
                    receive,
                    send,
                )

    asyncio.run(check())
    assert "请求取消" in logs() and "请求失败" not in logs()
    assert "previous-request" not in logs()


def test_stream_logs_business_failure_without_http_status_change(logs):
    async def failed():
        yield 'data: {"type":"RUN_ERROR","message":"failed"}\n\n'

    async def check():
        with log_context(trace_id="failed-run"):
            frames = [
                frame
                async for frame in observe_stream(
                    failed(), scene="mars", thread_id=None, run_id="run-failed"
                )
            ]
        assert len(frames) == 1

    asyncio.run(check())
    text = logs()
    assert "对话失败" in text and "run_id=run-failed" in text
    assert "对话完成" not in text


def test_cancelled_stream_closes_upstream_and_does_not_report_success(logs):
    cleaned = []

    async def source():
        try:
            yield 'data: {"type":"response_chunk","data":{"chunk":"hello"}}\n\n'
            await asyncio.sleep(60)
        finally:
            cleaned.append(True)

    async def check():
        stream = observe_stream(
            source(),
            scene="conversation",
            thread_id="conversation",
            run_id="cancel-run",
        )
        await anext(stream)
        await stream.aclose()
        assert cleaned == [True]

    asyncio.run(check())
    assert "对话取消" in logs() and "对话完成" not in logs()


def test_protocol_run_id_matches_logs_and_usage_is_aggregated(logs):
    from types import SimpleNamespace

    async def source():
        record_model_usage("model-a", 10, 5)
        yield {
            "type": "response_chunk",
            "data": {
                "chunk": "hello",
            },
        }

    async def check():
        with log_context(trace_id="trace-run", run_id="run-shared"):
            stream = protocol_stream(
                source(),
                SimpleNamespace(
                    headers={
                        "x-agentchat-protocol": "ag-ui/1.0",
                    }
                ),
                "conversation",
                "conversation-1",
            )
            events = [json.loads(frame[6:]) async for frame in stream]
        assert events[0]["runId"] == "run-shared"
        assert events[-1]["type"] == "RUN_FINISHED"

    asyncio.run(check())
    text = logs()
    assert "模型首个响应" in text
    completed = next(line for line in text.splitlines() if "对话完成" in line)
    assert "input_tokens=10" in completed and "output_tokens=5" in completed
    assert (
        "conversation_id=conversation-1" in completed
        and "run_id=run-shared" in completed
    )


def test_tool_error_result_is_logged_as_failure(logs):
    with tool_operation(
        "mcp.tool", tool="weather", server="maps", tool_call_id="tool-1"
    ) as operation:
        operation["failed"] = True
    text = logs()
    assert "工具调用开始" in text and "工具调用失败" in text
    assert "工具调用完成" not in text
    assert "tool_call_id=tool-1" in text


def test_rotation_and_reconfiguration_do_not_duplicate_entries(tmp_path):
    configure_logging(directory=tmp_path, console=False, rotation="1 KB")
    for _ in range(20):
        log_event("test", "轮转测试" + "x" * 200)
    logger.complete()
    assert list(tmp_path.glob("app.*.zip"))
    configure_logging(directory=tmp_path, console=False)
    log_event("test", "唯一记录")
    logger.complete()
    assert (tmp_path / "app.log").read_text(encoding="utf-8").count("唯一记录") == 1
    logger.remove()
