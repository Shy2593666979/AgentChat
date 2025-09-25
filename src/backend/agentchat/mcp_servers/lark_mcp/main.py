import argparse
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from mcp.server.fastmcp import FastMCP

from lark_mcp.mcp_server import register_mcp_server

mcp = FastMCP("Lark MCP Server")

register_mcp_server(mcp)


def health_check(request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route('/health', health_check, methods=["GET"]),
        Mount('/', app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lark MCP Server")
    parser.add_argument("--transport", type=str, default="sse", choices=["sse", "stdio", "streamable-http"],
                        help="Transport type")
    args = parser.parse_args()
    mcp.run(transport=args.transport)
