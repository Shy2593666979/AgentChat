import time
from contextvars import ContextVar

mars_tool_id = ContextVar("mars_tool_id", default="")


def get_mars_writer():
    """给各工具的子步骤附加调用标识，并行执行时也能归入正确的过程卡片。"""
    from langgraph.config import get_stream_writer
    writer = get_stream_writer()
    def emit(event):
        writer(
            {
                **event,
                "tool_id": mars_tool_id.get(),
            }
        )
    return emit


def progress(message, status="start"):
    return {
        "type": "progress_chunk",
        "time": time.time(),
        "data": {
            "message": message,
            "status": status,
        },
    }


def deep_search_event(chunk):
    """将深度搜索的执行状态与结果正文分开，避免日志混入下载文档。"""
    kind = chunk.get("type")
    content = chunk.get("content", "")
    if not content:
        return None
    if kind == "streaming":
        return {
            "type": "response_chunk",
            "time": time.time(),
            "data": content,
        }
    if kind in ("start", "complete", "error"):
        return {
            "type": "progress_chunk",
            "time": time.time(),
            "data": {
                "node": chunk.get("node", "unknown"),
                "status": kind,
                "message": content,
            },
        }
    # final_result 是已经流式发送过的完整正文，不重复追加。
    return None


async def stream_search_report(graph, messages, writer):
    """向页面发送正文，同时把完整结果返回给调度模型，避免把已完成的搜索当作空结果。"""
    report = ""
    async for chunk in graph.run_with_streaming(messages):
        if chunk.get("type") == "start" and chunk.get("node") == "finalize_answer":
            report = ""
            writer(
                {
                    "type": "result_start",
                    "result_key": "deep_search",
                    "data": {},
                }
            )
        event = deep_search_event(chunk)
        if event:
            if event["type"] == "response_chunk":
                report += event["data"]
                event["result_key"] = "deep_search"
            writer(event)
    return report
