import uuid
from fastapi import APIRouter, Depends

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.database.dao.register_task import RegisterMcpTaskDao
from agentchat.schemas.register_mcp import DeleteMcpTaskRequest
from agentchat.schemas.response import resp_200

router = APIRouter(prefix="/mcp/register", tags=["Register-Task"])

@router.get("/task/list")
async def get_register_mcp_tasks(
    login_user: UserPayload = Depends(get_login_user)
):
    tasks = await RegisterMcpTaskDao.get_all_tasks(login_user.user_id)
    result = [task.model_dump() for task in tasks]
    result.sort(key=lambda x: x["updated_time"], reverse=True)
    return resp_200(data=result)


@router.post("/task/create")
async def create_register_mcp_task(
    login_user: UserPayload = Depends(get_login_user)
):
    task_id = str(uuid.uuid4())
    task = await RegisterMcpTaskDao.create_task_if_not_exists(task_id, login_user.user_id)
    return resp_200(data=task.model_dump())


@router.post("/task/delete")
async def delete_register_mcp_task(
    req: DeleteMcpTaskRequest,
    login_user: UserPayload = Depends(get_login_user)
):
    result = await RegisterMcpTaskDao.delete_task(req.task_id)
    return resp_200(data=result)

