"""校验 config/mcp_server.json 中的 Parallel 搜索条目可被自动加载（离线运行）。

运行方式（在 src/backend 目录下）：
    python -m unittest agentchat.test.test_parallel_search_mcp
"""

import json
import unittest
from pathlib import Path

import httpx

from agentchat.schemas.mcp import MCPStreamableHttpConfig
from agentchat.services.mcp.manager import MCPManager
from agentchat.utils.convert import convert_mcp_config

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "mcp_server.json"
SERVER_NAME = "Parallel 搜索"
SERVER_URL = "https://search.parallel.ai/mcp"
EXPECTED_TOOLS = ["web_search", "web_fetch"]


def load_servers() -> list[dict]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


class McpServerConfigTests(unittest.TestCase):
    def test_every_entry_has_the_fields_init_data_reads(self) -> None:
        required = {
            "server_name",
            "url",
            "type",
            "config",
            "params",
            "config_enabled",
            "logo_url",
        }
        names = []
        for server in load_servers():
            self.assertLessEqual(required, set(server), server)
            self.assertIn(server["type"], {"sse", "streamable_http", "websocket"})
            self.assertIsInstance(server["config_enabled"], bool)
            names.append(server["server_name"])
        self.assertEqual(len(names), len(set(names)), "server_name must be unique")

    def test_parallel_entry_is_keyless_streamable_http(self) -> None:
        server = next(s for s in load_servers() if s["server_name"] == SERVER_NAME)
        self.assertEqual(server["url"], SERVER_URL)
        self.assertEqual(server["type"], "streamable_http")
        # 匿名端点不需要 API Key，因此无需用户单独配置参数
        self.assertEqual(server["config"], {})
        self.assertFalse(server["config_enabled"])

    def test_parallel_entry_converts_to_a_streamable_http_config(self) -> None:
        server = next(s for s in load_servers() if s["server_name"] == SERVER_NAME)
        config = convert_mcp_config(
            {
                "type": server["type"],
                "url": server["url"],
                "server_name": server["server_name"],
            }
        )
        self.assertIsInstance(config, MCPStreamableHttpConfig)
        self.assertEqual(config.transport, "streamable_http")
        self.assertEqual(config.url, SERVER_URL)


class ParallelServerLoadingTests(unittest.IsolatedAsyncioTestCase):
    """用模拟的 HTTP MCP 服务跑通加载流程，默认 CI 不访问网络。"""

    def setUp(self) -> None:
        self.requests = []
        server = next(s for s in load_servers() if s["server_name"] == SERVER_NAME)
        self.manager = MCPManager(
            convert_mcp_config(
                [
                    {
                        "type": server["type"],
                        "url": server["url"],
                        "server_name": server["server_name"],
                    }
                ]
            )
        )
        connection = self.manager.multi_server_client.connections[SERVER_NAME]
        connection["httpx_client_factory"] = self.http_client

    def http_client(self, headers=None, timeout=None, auth=None) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            auth=auth,
            transport=httpx.MockTransport(self.respond),
        )

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.assertEqual(str(request.url), SERVER_URL)
        self.assertNotIn("authorization", request.headers)
        if request.method != "POST":
            return httpx.Response(405)
        message = json.loads(request.content)
        self.requests.append(message)
        method = message["method"]
        if method == "notifications/initialized":
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "parallel-fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": name,
                        "description": "Fixture tool",
                        "inputSchema": {"type": "object", "properties": {}},
                    }
                    for name in EXPECTED_TOOLS
                ]
            }
        else:
            self.fail(f"Unexpected MCP method: {method}")
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": message["id"], "result": result}
        )

    async def test_show_mcp_tools_discovers_the_parallel_tools(self) -> None:
        servers = await self.manager.show_mcp_tools()
        self.assertEqual(list(servers), [SERVER_NAME])
        self.assertEqual([t["name"] for t in servers[SERVER_NAME]], EXPECTED_TOOLS)
        self.assertTrue(any(r["method"] == "initialize" for r in self.requests))


if __name__ == "__main__":
    unittest.main()
