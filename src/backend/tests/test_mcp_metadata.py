"""验证默认配置加载与后台异步生成，不连接远端 MCP，也不使用真实模型凭据。"""
import ast
import asyncio
import copy
import json
import re
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1] / "agentchat"


def load_definitions(path, names, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tree.body = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    exec(compile(tree, str(path), "exec"), namespace)


class MetadataTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = SimpleNamespace(
            server_name="Example",
            url="https://example.com/mcp",
            type="sse",
            imported_config={
                "mcpServers": {
                    "other": {
                        "headers": {
                            "X-Key": "test",
                        },
                    },
                },
            },
            mcp_as_tool_name="original_tool",
            description="original",
            tools=[],
            params=[],
        )
        self.records = {
            "server": self.server,
        }

        @contextmanager
        def session_getter():
            yield SimpleNamespace(get=lambda model, key: self.records.get(key),
                                  add=lambda obj: None, commit=lambda: None)

        self.manager = Mock()
        self.manager.return_value.show_mcp_tools = AsyncMock(
            return_value={
                "Example": [
                    {
                        "name": "search",
                        "input_schema": {},
                    }
                ],
            }
        )
        self.agent = Mock()
        self.agent.return_value.get_structured_response.return_value = SimpleNamespace(
            mcp_as_tool_name="example_web_search", description="Generated description")
        self.ns = dict(
            asyncio=asyncio,
            json=json,
            re=re,
            uuid4=uuid4,
            logger=Mock(),
            MCPServerTable=object,
            session_getter=session_getter,
            StructuredResponseAgent=self.agent,
            McpAsToolPrompt="{tools_info}",
            MCPResponseFormat=object,
            MCPManager=self.manager,
            convert_mcp_config=lambda value: value,
            _tasks={},
            _jobs={},
            _limit=asyncio.Semaphore(3),
        )
        tree = ast.parse((ROOT / "services/mcp/metadata.py").read_text(encoding="utf-8"))
        names = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        load_definitions(ROOT / "services/mcp/metadata.py", names, self.ns)

    async def asyncTearDown(self):
        await self.ns["stop_metadata_tasks"]()

    async def settle(self):
        await asyncio.gather(*list(self.ns["_tasks"].values()))

    async def test_model_is_background_and_does_not_block_event_loop(self):
        started, release = threading.Event(), threading.Event()
        result = self.agent.return_value.get_structured_response.return_value

        def blocking_model(*args):
            started.set()
            release.wait(2)
            return result

        self.agent.return_value.get_structured_response.side_effect = blocking_model
        self.ns["queue_metadata"]("server")
        self.assertEqual(self.ns["metadata_statuses"]()["server"]["metadata_status"], "pending")
        try:
            self.assertTrue(await asyncio.to_thread(started.wait, 1))
            await asyncio.wait_for(asyncio.sleep(0.01), 0.1)
            self.assertEqual(self.server.mcp_as_tool_name, "original_tool")
        finally:
            release.set()
        await self.settle()
        self.assertEqual(self.server.mcp_as_tool_name, "example_web_search")
        self.assertEqual(self.server.tools, ["search"])
        self.assertEqual(
            self.manager.call_args.args[0][0]["headers"],
            {
                "X-Key": "test",
            },
        )
        self.assertEqual(self.ns["metadata_statuses"]()["server"]["metadata_status"], "ready")

    async def test_failed_discovery_does_not_generate_or_overwrite(self):
        self.manager.return_value.show_mcp_tools.return_value = {}
        self.ns["queue_metadata"]("server")
        await self.settle()
        self.agent.assert_not_called()
        self.assertEqual(self.server.description, "original")
        self.assertEqual(self.ns["metadata_statuses"]()["server"]["metadata_status"], "failed")

    async def test_old_response_and_deleted_service_cannot_be_written(self):
        self.ns["_jobs"]["server"] = {
            "token": "new",
            "status": "running",
            "error": "",
        }
        self.ns["_finish"](
            "server",
            "old",
            {
                "description": "stale",
            },
        )
        self.assertEqual(self.server.description, "original")
        self.records.clear()
        self.ns["_finish"](
            "server",
            "new",
            {
                "description": "deleted",
            },
        )
        self.assertEqual(self.records, {})

    async def test_user_creation_returns_before_generation_and_saves_import(self):
        ns = dict(
            Dict=Dict,
            Any=Any,
            uuid4=uuid4,
            queue_metadata=Mock(),
            metadata_statuses=Mock(),
            forget_metadata=Mock(),
            app_settings=SimpleNamespace(default_config={}),
        )
        load_definitions(ROOT / "api/services/mcp_server.py", {"MCPService"}, ns)
        service = ns["MCPService"]
        service.create_mcp_server = AsyncMock(return_value="new-server")
        config = {
            "mcpServers": {
                "Example": {
                    "url": self.server.url,
                    "type": "sse",
                    "headers": {
                        "X-Key": "test",
                    },
                },
            },
        }
        server_id = await service.create_user_mcp_server(
            {
                "server_name": "Example",
                "url": self.server.url,
                "type": "sse",
            },
            "user",
            "User",
            imported_config=config,
        )
        self.assertEqual(server_id, "new-server")
        self.assertEqual(service.create_mcp_server.call_args.kwargs["imported_config"], config)
        ns["queue_metadata"].assert_called_once_with("new-server")


class DefaultMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_defaults_load_without_network_are_idempotent_and_preserve_existing_records(self):
        configs = json.loads((ROOT / "config/mcp_server.json").read_text(encoding="utf-8"))
        self.assertEqual(len(configs), 3)
        self.assertTrue(all(config["mcp_as_tool_name"] and config["description"] for config in configs))
        records = [SimpleNamespace(mcp_server_id="old-feishu", user_id="0", server_name="飞书", url="http://47.95.23.87:8000/sse"),
                   SimpleNamespace(mcp_server_id="personal-feishu", user_id="user", server_name="飞书", url="http://47.95.23.87:8000/sse")]

        async def create(**data):
            records.append(SimpleNamespace(mcp_server_id=uuid4().hex, **data))

        async def delete(server_id):
            records[:] = [row for row in records if row.mcp_server_id != server_id]

        async def update(server_id, data):
            row = next(row for row in records if row.mcp_server_id == server_id)
            for key, value in data.items():
                setattr(row, key, value)

        async def get_system(user_id):
            return [copy.copy(row) for row in records if row.user_id == user_id]

        service = SimpleNamespace(create_mcp_server=AsyncMock(side_effect=create), delete_server_from_id=AsyncMock(side_effect=delete),
                                  update_mcp_server=AsyncMock(side_effect=update))
        ns = dict(
            load_json=AsyncMock(return_value=configs),
            SystemUser="0",
            logger=Mock(),
            MCPServerDao=SimpleNamespace(
                get_mcp_servers_from_user=AsyncMock(side_effect=get_system),
                create_mcp_server=service.create_mcp_server,
            ),
        )
        load_definitions(ROOT / "database/init_data.py", {"_init_system_mcp_server"}, ns)
        await ns["_init_system_mcp_server"]()
        ids = [row.mcp_server_id for row in records]
        await ns["_init_system_mcp_server"]()
        self.assertEqual([row.mcp_server_id for row in records], ids)
        service.create_mcp_server.assert_awaited()
        self.assertEqual(service.create_mcp_server.await_count, 3)
        service.update_mcp_server.assert_not_awaited()
        self.assertIn("personal-feishu", ids)
        self.assertIn("old-feishu", ids)
        service.delete_server_from_id.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
