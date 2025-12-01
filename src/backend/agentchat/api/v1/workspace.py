import json
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from starlette.responses import StreamingResponse

from agentchat.api.services.llm import LLMService
from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.tool import ToolService
from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.prompts.chat import SYSTEM_PROMPT
from agentchat.schema.schemas import resp_200
from agentchat.schema.usage_stats import UsageStatsAgentType
from agentchat.schema.workspace import WorkSpaceSimpleTask
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.services.workspace.simple_agent import WorkSpaceSimpleAgent, MCPConfig
from agentchat.utils.contexts import set_user_id_context, set_agent_name_context
from agentchat.utils.convert import convert_mcp_config

router = APIRouter(prefix="/workspace", tags=["WorkSpace"])


@router.get("/plugins", summary="获取工作台的可用插件")
async def get_workspace_plugins(login_user: UserPayload = Depends(get_login_user)):
    results = await ToolService.get_visible_tool_by_user(login_user.user_id)
    return resp_200(data=results)

@router.get("/session", summary="获取工作台所有会话列表")
async def get_workspace_sessions(login_user: UserPayload = Depends(get_login_user)):
    results = await WorkSpaceSessionService.get_workspace_sessions(login_user.user_id)
    return resp_200(data=results)


@router.post("/session", summary="创建工作台会话")
async def create_workspace_session(*,
                                   title: str = "",
                                   contexts: dict = {},
                                   login_user: UserPayload = Depends(get_login_user)):
    pass

@router.post("/session/{session_id}", summary="进入工作台会话")
async def workspace_session_info(session_id: str,
                                 login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await WorkSpaceSessionService.get_workspace_session_from_id(session_id, login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@router.delete("/session", summary="删除工作台的会话")
async def create_workspace_session(session_id: str,
                                   login_user: UserPayload = Depends(get_login_user)):
    try:
        await WorkSpaceSessionService.delete_workspace_session([session_id], login_user.user_id)
        return resp_200()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/simple/chat", summary="工作台日常对话")
async def workspace_simple_chat(simple_task: WorkSpaceSimpleTask,
                                login_user: UserPayload = Depends(get_login_user)):
    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.simple_agent)

    model_config = await LLMService.get_llm_by_id(simple_task.model_id)
    servers_config = []
    for mcp_id in simple_task.mcp_servers:
        mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
        servers_config.append(
            MCPConfig(**mcp_server)
        )

    simple_agent = WorkSpaceSimpleAgent(
        model_config={
            "model": model_config["model"],
            "base_url": model_config["base_url"],
            "api_key": model_config["api_key"],
            "user_id": login_user.user_id,
        },
        mcp_configs=servers_config,
        plugins=simple_task.plugins,
        user_id=login_user.user_id,
        session_id=simple_task.session_id
    )

    workspace_session = await WorkSpaceSessionService.get_workspace_session_from_id(simple_task.session_id, login_user.user_id)
    if workspace_session:
        contexts = workspace_session.get("contexts", [])
        history_messages = [f"query: {message.get("query")}, answer: {message.get("answer")}\n" for message in contexts]
    else:
        history_messages = "无历史对话"

    async def general_generate():
        async for chunk in simple_agent.astream([SystemMessage(content=SYSTEM_PROMPT.format(history=str(history_messages))), HumanMessage(content=simple_task.query)]):
            # chunk 已经是 dict: {"event": "task_result", "data": {"message": "..."}}
            # 需要 JSON 序列化后作为 SSE 的 data 字段
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        general_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


