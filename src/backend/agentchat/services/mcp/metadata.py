import asyncio
import json
import re
from uuid import uuid4

from loguru import logger

from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.database.models.mcp_server import MCPServerTable
from agentchat.database.session import session_getter
from agentchat.prompts.mcp import McpAsToolPrompt
from agentchat.schemas.mcp import MCPResponseFormat
from agentchat.services.mcp.manager import MCPManager
from agentchat.utils.convert import convert_mcp_config

_tasks: dict[tuple[str, str], asyncio.Task] = {}
_jobs: dict[str, dict] = {}
_limit = asyncio.Semaphore(3)


def metadata_statuses() -> dict:
    return {
        server_id: {
            "metadata_status": job["status"],
            "metadata_error": job["error"],
        }
        for server_id, job in _jobs.items()
    }


def queue_metadata(server_id: str, updates: dict | None = None) -> None:
    """直接在当前进程中异步执行，不创建任务表，也不在启动时自动刷新。"""
    token = uuid4().hex
    with session_getter() as session:
        server = session.get(MCPServerTable, server_id)
        if server is None:
            raise ValueError("服务不存在")
        for key, value in (updates or {}).items():
            setattr(server, key, value)
        session.add(server)
        session.commit()
    _jobs[server_id] = {
        "token": token,
        "status": "pending",
        "error": "",
    }
    _schedule(server_id, token)


def _schedule(server_id: str, token: str) -> None:
    key = server_id, token
    if key not in _tasks:
        task = asyncio.create_task(_generate(server_id, token))
        _tasks[key] = task
        task.add_done_callback(lambda _: _tasks.pop(key, None))


def forget_metadata(server_id: str) -> None:
    _jobs.pop(server_id, None)
    for (task_server_id, _), task in list(_tasks.items()):
        if task_server_id == server_id:
            task.cancel()


async def stop_metadata_tasks() -> None:
    tasks = list(_tasks.values())
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def _finish(server_id: str, token: str, updates: dict | None, error: str = "") -> None:
    with session_getter() as session:
        job = _jobs.get(server_id)
        server = session.get(MCPServerTable, server_id)
        # 服务已删除或配置已更新时，不允许旧任务的模型结果覆盖当前数据。
        if job is None or server is None or job["token"] != token:
            return
        if updates:
            for key, value in updates.items():
                setattr(server, key, value)
            session.add(server)
        session.commit()
        job["status"], job["error"] = ("failed", error) if error else ("ready", "")


async def _generate(server_id: str, token: str) -> None:
    try:
        async with _limit, asyncio.timeout(120):
            with session_getter() as session:
                server = session.get(MCPServerTable, server_id)
                job = _jobs.get(server_id)
                if server is None or job is None or job["token"] != token:
                    return
                config = next(iter((server.imported_config or {}).get("mcpServers", {}).values()), {})
                info = {
                    "server_name": server.server_name,
                    "url": server.url,
                    "type": server.type,
                    "headers": config.get("headers"),
                }
                job["status"] = "running"
            params = await MCPManager([convert_mcp_config(info)]).show_mcp_tools()
            if info["server_name"] not in params:
                raise ValueError("MCP tool discovery failed")
            # 同步模型调用放到独立线程中执行，避免阻塞 HTTP 服务的事件循环。
            def generate():
                return StructuredResponseAgent(MCPResponseFormat).get_structured_response(
                    McpAsToolPrompt.format(tools_info=json.dumps(params, ensure_ascii=False)))
            result = await asyncio.to_thread(generate)
            if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", result.mcp_as_tool_name) or not result.description.strip():
                raise ValueError("Invalid MCP metadata")
            tools = params[info["server_name"]]
            _finish(
                server_id,
                token,
                {
                    "mcp_as_tool_name": result.mcp_as_tool_name,
                    "description": result.description,
                    "tools": [tool["name"] for tool in tools],
                    "params": tools,
                },
            )
    except asyncio.CancelledError:
        _finish(server_id, token, None, "生成已中断，请重试。")
        raise
    except Exception as error:
        logger.warning("MCP metadata generation failed for {} ({})", server_id, type(error).__name__)
        _finish(server_id, token, None, "工具发现或描述生成失败，请检查服务连接和模型配置后重试。")
