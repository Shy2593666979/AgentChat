from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse

from agentchat.api.services.tool import ToolService
from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.schema.schemas import resp_200
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.database.models.workspace_session import WorkSpaceSessionCreate
from agentchat.services.lingseek.agent import LingSeekAgent

router = APIRouter(prefix="/workspace")


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

