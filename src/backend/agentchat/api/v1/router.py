from fastapi import APIRouter
from agentchat.api.v1 import (
    completion, dialog, message, agent, history, mars,
    user, llm, tool, knowledge, knowledge_file, mcp_server, mcp_user_config,
    workspace, lingseek, usage_stats, upload, wechat, agent_skill,
    register_mcp, register_mcp_completion, register_task
)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(completion.router)
api_v1_router.include_router(dialog.router)
api_v1_router.include_router(message.router)
api_v1_router.include_router(agent.router)
api_v1_router.include_router(history.router)
api_v1_router.include_router(user.router)
api_v1_router.include_router(tool.router)
api_v1_router.include_router(llm.router)
api_v1_router.include_router(knowledge.router)
api_v1_router.include_router(knowledge_file.router)
api_v1_router.include_router(mcp_server.router)
api_v1_router.include_router(mcp_user_config.router)
api_v1_router.include_router(mars.router)
api_v1_router.include_router(workspace.router)
api_v1_router.include_router(lingseek.router)
api_v1_router.include_router(usage_stats.router)
api_v1_router.include_router(wechat.router)
api_v1_router.include_router(upload.router)
api_v1_router.include_router(agent_skill.router)
api_v1_router.include_router(register_task.router)
api_v1_router.include_router(register_mcp.router)
api_v1_router.include_router(register_mcp_completion.router)