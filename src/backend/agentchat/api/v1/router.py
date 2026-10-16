from fastapi import APIRouter

from agentchat.api.v1 import (
    agent,
    agent_skill,
    completion,
    conversation,
    history,
    knowledge,
    knowledge_file,
    lingseek,
    llm,
    mars,
    mcp_server,
    mcp_user_config,
    message,
    register_mcp,
    register_mcp_completion,
    register_task,
    tool,
    upload,
    usage_stats,
    user,
    wechat,
    workspace,
)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(completion.router)
api_v1_router.include_router(conversation.router)
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