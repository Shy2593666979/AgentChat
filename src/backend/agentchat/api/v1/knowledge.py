from typing import Union, List
from loguru import logger
from fastapi import Body, APIRouter, Depends

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.knowledge import KnowledgeCreateRequest, KnowledgeUpdateRequest
from agentchat.schema.schemas import UnifiedResponseModel, resp_500, resp_200
from agentchat.services.rag_handler import RagHandler

router = APIRouter(tags=["Knowledge"])


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
        # 验证用户权限
        await KnowledgeService.verify_user_permission(knowledge_req.knowledge_id, login_user.user_id)

        await KnowledgeService.update_knowledge(knowledge_req.knowledge_id, knowledge_req.knowledge_name,
                                                knowledge_req.knowledge_desc)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/knowledge/delete", response_model=UnifiedResponseModel)
async def delete_knowledge(knowledge_id: str = Body(embed=True),
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await KnowledgeService.verify_user_permission(knowledge_id, login_user.user_id)

        await KnowledgeService.delete_knowledge(knowledge_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))

@router.post("/knowledge/retrieval", response_model=UnifiedResponseModel)
async def retrieval_knowledge(*,
                              query: str = Body(..., description="用户的问题"),
                              knowledge_id: Union[str, List[str]] = Body(..., description="知识库ID")):
    if isinstance(knowledge_id, str):
        content = await RagHandler.retrieve_ranked_documents(query, [knowledge_id], [knowledge_id])
    else:
        content = await RagHandler.retrieve_ranked_documents(query, knowledge_id, knowledge_id)
    return resp_200(content)
