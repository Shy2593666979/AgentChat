from loguru import logger
from fastapi import Body, APIRouter, Depends

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.knowledge import KnowledgeCreateRequest, KnowledgeUpdateRequest
from agentchat.schema.schemas import UnifiedResponseModel, resp_500, resp_200

router = APIRouter()


@router.post("/knowledge/create", response_model=UnifiedResponseModel)
async def upload_knowledge(*,
                           knowledge_req: KnowledgeCreateRequest,
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeService.create_knowledge(knowledge_req.knowledge_name, knowledge_req.knowledge_desc,
                                                login_user.user_id)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))


@router.get("/knowledge/select", response_model=UnifiedResponseModel)
async def select_knowledge(login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await KnowledgeService.select_knowledge(login_user.user_id)
        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/knowledge/update", response_model=UnifiedResponseModel)
async def update_knowledge(*,
                           knowledge_req: KnowledgeUpdateRequest,
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeService.update_knowledge(knowledge_req.knowledge_id, knowledge_req.knowledge_name,
                                                knowledge_req.knowledge_desc, login_user.user_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/knowledge/delete", response_model=UnifiedResponseModel)
async def delete_knowledge(knowledge_id: str = Body(embed=True),
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeService.delete_knowledge(knowledge_id, login_user.user_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
