from fastapi import APIRouter, Depends

from agentchat.api.services.user import UserPayload, get_login_user

router = APIRouter(prefix="/workbench")

@router.get("/session", summary="获取工作台所有会话列表")
async def get_workbench_sessions(login_user: UserPayload = Depends(get_login_user)):
    pass

@router.post("/session", summary="创建工作台会话")
async def create_workbench_session():

    pass

@router.post("/session/{session_id}", summary="进入工作台会话")
async def workbench_session_info(session_id: str,
                                 login_user: UserPayload = Depends(get_login_user)):
    pass

@router.post("/session/delete", summary="删除工作台的会话")
async def create_workbench_session():
    pass