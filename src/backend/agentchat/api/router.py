from fastapi import APIRouter
from agentchat.api.v1 import (chat, dialog, message, agent, history, mcp_stdio_server, mcp_chat, mars,
                              user, llm, tool, knowledge, knowledge_file, mcp_agent, mcp_server, mcp_user_config,
                              workspace, lingseek, usage_stats, upload, wechat)

router = APIRouter(prefix="/api/v1")

router.include_router(chat.router)
router.include_router(dialog.router)
router.include_router(message.router)
router.include_router(agent.router)
router.include_router(history.router)
router.include_router(user.router)
router.include_router(tool.router)
router.include_router(llm.router)
router.include_router(knowledge.router)
router.include_router(knowledge_file.router)
router.include_router(mcp_server.router)
router.include_router(mcp_stdio_server.router)
router.include_router(mcp_chat.router)
router.include_router(mcp_agent.router)
router.include_router(mcp_user_config.router)
router.include_router(mars.router)
router.include_router(workspace.router)
router.include_router(lingseek.router)
router.include_router(usage_stats.router)
router.include_router(wechat.router)
router.include_router(upload.router)