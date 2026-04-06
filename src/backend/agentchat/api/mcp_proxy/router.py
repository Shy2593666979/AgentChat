from fastapi import APIRouter
from agentchat.api.mcp_proxy.mcp_sse import router as mcp_sse_router
from agentchat.api.mcp_proxy.mcp_streamable_http import router as mcp_streamable_http_router


mcp_proxy_router = APIRouter()

mcp_proxy_router.include_router(mcp_sse_router)
mcp_proxy_router.include_router(mcp_streamable_http_router)

