from loguru import logger
from fastapi import Body, APIRouter, Depends

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.schemas import UnifiedResponseModel, resp_500, resp_200

router = APIRouter()

@router.post("/knowledge/create", response_model=UnifiedResponseModel)
async def upload_knowledge(knowledge_name: str = Body(alias='name'),
                           knowledge_desc: str = Body(alias='description'),
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeService.create_knowledge(knowledge_name, knowledge_desc, login_user.user_id)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))

@router.get("/knowledge/select", response_model=UnifiedResponseModel)
async def select_knowledge(login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await KnowledgeService.select_user_by_id(login_user.user_id)

        knowledge_data = []
        for result in results:
            knowledge_data.append({
                'id': result.id,
                'name': result.name,
                'description': result.description,
                'user_id': result.user_id,
                'update_time': result.update_time
            })
        return resp_200(data=knowledge_data)
    except Exception as err:
        return resp_500(message=str(err))

@router.put("/knowledge/update", response_model=UnifiedResponseModel)
async def update_knowledge(knowledge_id: str = Body(alias='id'),
                           knowledge_name: str = Body(alias='name'),
                           knowledge_desc: str = Body(alias='description'),
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeService.update_knowledge(knowledge_id, knowledge_name, knowledge_desc, login_user.user_id)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))

@router.delete("/knowledge/delete", response_model=UnifiedResponseModel)
async def delete_knowledge(knowledge_id: str = Body(alias='id'),
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeService.delete_knowledge(knowledge_id, login_user.user_id)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))

