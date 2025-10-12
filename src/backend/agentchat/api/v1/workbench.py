from fastapi import APIRouter, Depends, HTTPException

from agentchat.api.services.workbench_session import WorkBenchSessionService
from agentchat.schema.schemas import resp_200
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.database.models.workbench_session import WorkBenchSessionCreate

router = APIRouter(prefix="/workbench")

@router.get("/session", summary="获取工作台所有会话列表")
async def get_workbench_sessions(login_user: UserPayload = Depends(get_login_user)):
    results = await WorkBenchSessionService.get_workbench_sessions(login_user.user_id)
    return resp_200(data=results)


@router.post("/session", summary="创建工作台会话")
async def create_workbench_session(*,
                                   title: str = "",
                                   contexts: dict = {},
                                   login_user: UserPayload = Depends(get_login_user)):
    pass

@router.post("/session/{session_id}", summary="进入工作台会话")
async def workbench_session_info(session_id: str,
                                 login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await WorkBenchSessionService.get_workbench_session_from_id(session_id, login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@router.post("/session/delete", summary="删除工作台的会话")
async def create_workbench_session(session_id: str,
                                   login_user: UserPayload = Depends(get_login_user)):
    try:
        await WorkBenchSessionService.delete_workbench_session([session_id], login_user.user_id)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
