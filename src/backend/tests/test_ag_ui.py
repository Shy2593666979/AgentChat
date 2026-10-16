"""用 SDK 校验真实编码输出，覆盖并发、审批、失败和停止时的清理。"""
import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from ag_ui.core import Event
from agentchat.protocols.ag_ui.conversation import ConversationAdapter
from agentchat.protocols.ag_ui.mars import MarsAdapter
from agentchat.protocols.ag_ui.mcp import McpAdapter
from agentchat.protocols.ag_ui.streaming import encode_stream, protocol_stream
from agentchat.protocols.ag_ui.workspace import WorkspaceAdapter
from pydantic import TypeAdapter

validator = TypeAdapter(Event)


async def source(events):
    for event in events:
        yield event


async def collect(events, adapter):
    frames = [frame async for frame in encode_stream(source(events), adapter)]
    result = [json.loads(frame.removeprefix("data: ").strip()) for frame in frames]
    for event in result:
        validator.validate_python(event)
    return result


def test_conversation_parallel_tools_and_identity():
    async def check():
        events = [
            {
                "type": "agent",
                "data": {
                    "agent_id": "agent-a",
                    "name": "资料助手",
                },
            }
        ]
        for identity in ("first", "second"):
            events.append(
                {
                    "type": "event",
                    "data": {
                        "tool_call_id": identity,
                        "tool_name": "search",
                        "title": "搜索",
                        "status": "START",
                        "args": {
                            "q": identity,
                        },
                    },
                }
            )
        for identity in ("second", "first"):
            events.append(
                {
                    "type": "event",
                    "data": {
                        "tool_call_id": identity,
                        "tool_name": "search",
                        "title": "搜索",
                        "status": "END",
                        "message": identity,
                    },
                }
            )
        events.extend(
            [
                {
                    "type": "response_chunk",
                    "data": {
                        "chunk": "你",
                    },
                },
                {
                    "type": "response_chunk",
                    "data": {
                        "chunk": "好",
                    },
                },
            ]
        )
        stream = await collect(events, ConversationAdapter("conversation-a"))
        assert stream[0]["threadId"] == "conversation-a"
        assert stream[1]["name"] == "agentchat.agent"
        results = [event for event in stream if event["type"] == "TOOL_CALL_RESULT"]
        assert [(event["toolCallId"], event["content"]) for event in results] == [("second", "second"), ("first", "first")]
        assert stream[-1]["type"] == "RUN_FINISHED"
        for identity in ("first", "second"):
            kinds = [event["type"] for event in stream if event.get("toolCallId") == identity]
            assert kinds == ["TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "TOOL_CALL_RESULT"]
        assert "".join(event["delta"] for event in stream if event["type"] == "TEXT_MESSAGE_CONTENT") == "你好"
    asyncio.run(check())


def test_run_failure_and_explicit_model_error_are_terminal():
    async def failing():
        yield {
            "type": "response_chunk",
            "data": {
                "chunk": "部分内容",
            },
        }
        raise RuntimeError("internal-secret-must-not-be-sent")

    async def check():
        frames = [json.loads(frame[6:]) async for frame in encode_stream(failing(), ConversationAdapter("conversation"))]
        assert frames[-1]["type"] == "RUN_ERROR"
        assert "internal-secret" not in json.dumps(frames)
        assert not any(event["type"] == "RUN_FINISHED" for event in frames)
        explicit = await collect(
            [
                {
                    "type": "error",
                    "data": {
                        "message": "模型不可用",
                    },
                }
            ],
            ConversationAdapter("conversation"),
        )
        assert explicit[-1]["type"] == "RUN_ERROR"
    asyncio.run(check())


def test_stop_closes_upstream_without_success_event():
    saved = []

    async def business():
        try:
            yield {
                "type": "response_chunk",
                "data": {
                    "chunk": "部分回复",
                },
            }
            await asyncio.sleep(60)
        finally:
            saved.append("已保存并清理")

    async def check():
        stream = encode_stream(business(), ConversationAdapter("conversation"))
        frames = []
        while True:
            event = json.loads((await anext(stream))[6:])
            frames.append(event)
            if event["type"] == "TEXT_MESSAGE_CONTENT":
                break
        await stream.aclose()
        assert saved == ["已保存并清理"]
        assert not any(event["type"] == "RUN_FINISHED" for event in frames)
    asyncio.run(check())


def test_asgi_disconnect_closes_stream_and_runs_cleanup():
    from agentchat.api.responses.streaming import WatchedStreamingResponse
    from starlette.requests import ClientDisconnect
    cleaned = []

    async def business():
        try:
            yield {
                "type": "response_chunk",
                "data": {
                    "chunk": "部分内容",
                },
            }
        finally:
            cleaned.append(True)

    async def check():
        response = WatchedStreamingResponse(encode_stream(business(), ConversationAdapter("conversation")))
        async def receive():
            return {
                "type": "http.disconnect",
            }
        async def send(message):
            if message["type"] == "http.response.body" and b"TEXT_MESSAGE_CONTENT" in message["body"]:
                raise OSError("连接已关闭")
        with pytest.raises(ClientDisconnect):
            await response(
                {
                    "type": "http",
                    "asgi": {
                        "spec_version": "2.4",
                    },
                },
                receive,
                send,
            )
        assert cleaned == [True]
    asyncio.run(check())


def test_parallel_runs_do_not_share_ids():
    async def check():
        a, b = await asyncio.gather(
            *[
                collect(
                    [
                        {
                            "type": "response_chunk",
                            "data": {
                                "chunk": value,
                            },
                        }
                    ],
                    ConversationAdapter(value),
                )
                for value in ("a", "b")
            ]
        )
        assert a[0]["threadId"] == "a" and b[0]["threadId"] == "b"
        assert a[0]["runId"] != b[0]["runId"]
        assert a[1]["messageId"] != b[1]["messageId"]
    asyncio.run(check())


def test_mars_attribution_progress_reset_and_reasoning():
    stream = asyncio.run(
        collect(
            [
                {
                    "type": "reasoning_chunk",
                    "data": "正在分析",
                },
                {
                    "type": "tool_start",
                    "data": {
                        "id": "search-a",
                        "name": "deep_search",
                        "label": "深度搜索",
                    },
                },
                {
                    "type": "result_start",
                    "tool_id": "search-a",
                    "result_key": "deep_search",
                },
                {
                    "type": "progress_chunk",
                    "tool_id": "search-a",
                    "data": {
                        "status": "start",
                        "message": "检索中",
                    },
                },
                {
                    "type": "response_chunk",
                    "tool_id": "search-a",
                    "result_key": "deep_search",
                    "data": "搜索结果",
                },
                {
                    "type": "tool_end",
                    "data": {
                        "id": "search-a",
                        "elapsed": 1.5,
                    },
                },
            ],
            MarsAdapter(),
        )
    )
    assert any(event["type"] == "REASONING_MESSAGE_CONTENT" for event in stream)
    text = next(event for event in stream if event["type"] == "TEXT_MESSAGE_CONTENT")
    assert text["metadata"] == {
        "tool_id": "search-a",
        "result_key": "deep_search",
    }
    assert next(event for event in stream if event["type"] == "TOOL_CALL_RESULT")["metadata"]["elapsed"] == 1.5
    assert stream[-1]["type"] == "RUN_FINISHED"


def test_workspace_graph_step_and_guide_are_separate():
    stream = asyncio.run(
        collect(
            [
                {
                    "event": "generate_tasks",
                    "data": {
                        "graph": [
                            {
                                "start": "需求",
                                "end": "搜索",
                            }
                        ],
                    },
                },
                {
                    "event": "step_start",
                    "data": {
                        "title": "搜索",
                    },
                },
                {
                    "event": "step_result",
                    "data": {
                        "title": "搜索",
                        "message": "结果",
                    },
                },
                {
                    "event": "task_result",
                    "data": {
                        "message": "报告",
                    },
                },
            ],
            WorkspaceAdapter("workspace"),
        )
    )
    assert stream[1]["type"] == "STATE_SNAPSHOT"
    assert [event["type"] for event in stream if event["type"].startswith("STEP_")] == ["STEP_STARTED", "STEP_FINISHED"]
    assert next(event for event in stream if event["type"] == "TEXT_MESSAGE_CONTENT")["delta"] == "报告"


def test_mcp_interrupt_is_not_normal_completion_and_resume_keeps_thread():
    stream = asyncio.run(
        collect(
            [
                {
                    "type": "text",
                    "content": "请确认",
                },
                {
                    "type": "interrupt",
                    "event": {
                        "interrupt_id": "approval-1",
                        "allowed_decisions": ["approve", "reject"],
                        "action_requests": [
                            {
                                "name": "register",
                            }
                        ],
                    },
                },
            ],
            McpAdapter("task"),
        )
    )
    end = stream[-1]
    assert end["outcome"]["type"] == "interrupt"
    assert end["outcome"]["interrupts"][0]["id"] == "approval-1"
    resumed = asyncio.run(
        collect(
            [
                {
                    "type": "text",
                    "content": "注册成功",
                }
            ],
            McpAdapter("task"),
        )
    )
    assert resumed[-1]["outcome"]["type"] == "success"
    assert resumed[0]["threadId"] == stream[0]["threadId"]
    assert resumed[0]["runId"] != stream[0]["runId"]


def test_explicit_negotiation_preserves_legacy_frames():
    original = source([])
    async def legacy():
        return [frame async for frame in protocol_stream(original, None, "conversation")]
    assert asyncio.run(legacy()) == []
    original = source([])
    request = SimpleNamespace(
        headers={
            "x-agentchat-protocol": "ag-ui/1.0",
        }
    )
    adapted = protocol_stream(original, request, "conversation", "conversation")
    async def check():
        frames = [json.loads(frame[6:]) async for frame in adapted]
        assert frames[0]["type"] == "RUN_STARTED"
        assert frames[-1]["type"] == "RUN_FINISHED"
    asyncio.run(check())


@pytest.mark.parametrize("adapter", [ConversationAdapter, MarsAdapter, WorkspaceAdapter, McpAdapter])
def test_unmapped_events_fail_instead_of_silently_losing_content(adapter):
    events = asyncio.run(
        collect(
            [
                {
                    "type": "unknown",
                    "data": "不可丢失",
                }
            ],
            adapter(),
        )
    )
    assert events[-1]["type"] == "RUN_ERROR"


def test_frontend_consumes_python_sdk_events(tmp_path):
    frontend = Path(__file__).parents[2] / "frontend"
    if not shutil.which("node") or not (frontend / "node_modules/typescript").is_dir():
        pytest.skip("前端依赖未安装，跳过跨语言协议检查")
    samples = [
        (
            "/api/v1/completion",
            ConversationAdapter(),
            [
                {
                    "type": "response_chunk",
                    "data": {
                        "chunk": "你好",
                    },
                }
            ],
            ["response_chunk"],
        ),
        (
            "/api/v1/mars/chat",
            MarsAdapter(),
            [
                {
                    "type": "reasoning_chunk",
                    "data": "分析",
                },
                {
                    "type": "response_chunk",
                    "data": "结果",
                },
            ],
            ["reasoning_chunk", "response_chunk"],
        ),
        (
            "/api/v1/workspace/lingseek/task_start",
            WorkspaceAdapter(),
            [
                {
                    "event": "step_start",
                    "data": {
                        "title": "检索",
                    },
                },
                {
                    "event": "step_result",
                    "data": {
                        "title": "检索",
                        "message": "结果",
                    },
                },
                {
                    "event": "task_result",
                    "data": {
                        "message": "报告",
                    },
                },
            ],
            ["workspace_step", "workspace_text"],
        ),
        (
            "/api/v1/mcp/register/completion",
            McpAdapter(),
            [
                {
                    "type": "text",
                    "content": "确认",
                },
                {
                    "type": "interrupt",
                    "event": {
                        "interrupt_id": "approval",
                        "allowed_decisions": ["approve"],
                    },
                },
            ],
            ["text", "interrupt"],
        ),
    ]
    corpus = [
        {
            "url": url,
            "events": asyncio.run(collect(events, adapter)),
            "expected": expected,
        }
        for url, adapter, events, expected in samples
    ]
    fixture = tmp_path / "ag-ui.json"
    fixture.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    result = subprocess.run(
        ["node", "--test", "tests/ag-ui-stream.cjs"],
        cwd=frontend,
        env={
            **os.environ,
            "AG_UI_FIXTURE": str(fixture),
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
