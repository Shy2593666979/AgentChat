"""校验 Lark MCP 工具中默认值为 None 的参数可以显式传入 null（离线运行，不调用飞书接口）。

运行方式（在 src/backend 目录下）：
    python -m unittest agentchat.test.test_lark_mcp_optional_args
"""

import sys
import unittest
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp_servers"))

from lark_mcp.mcp_server import register_mcp_server


def _accepts_null(prop: dict) -> bool:
    if prop.get("type") == "null":
        return True
    return any(_accepts_null(option) for option in prop.get("anyOf", []))


class LarkMcpOptionalArgsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mcp = FastMCP("Lark MCP Server")
        register_mcp_server(self.mcp)
        self.tools = self.mcp._tool_manager.list_tools()

    def test_null_default_arguments_accept_null(self) -> None:
        checked = 0
        for tool in self.tools:
            for name, prop in tool.parameters.get("properties", {}).items():
                if "default" in prop and prop["default"] is None:
                    checked += 1
                    with self.subTest(tool=tool.name, argument=name):
                        self.assertTrue(_accepts_null(prop), prop)
        self.assertGreater(checked, 0)

    def test_explicit_null_passes_argument_validation(self) -> None:
        tool = self.mcp._tool_manager.get_tool("batch_get_user_info")
        args = tool.fn_metadata.arg_model.model_validate(
            {"emails": None, "mobiles": ["+8613800000000"], "app_id": None, "app_secret": None}
        )
        self.assertIsNone(args.emails)
        self.assertIsNone(args.app_id)


if __name__ == "__main__":
    unittest.main()
