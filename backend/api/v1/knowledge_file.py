from fastapi import FastAPI, APIRouter, Body, UploadFile, File, Depends

from services.oss import oss_client
from settings import app_settings
from loguru import logger
from api.services.knowledge_file import KnowledgeFileService
from api.services.user import get_login_user, UserPayload
from schema.schemas import UnifiedResponseModel, resp_200, resp_500
from utils.file_utils import save_upload_file, get_oss_object_name

router = APIRouter()


@router.post('/knowledge_file/create', response_model=UnifiedResponseModel)
async def upload_file(knowledge_id: str = Body(...),
                      file: UploadFile = File(...),
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        file_path = await save_upload_file(file)
        if app_settings.use_oss:
            object_name = await get_oss_object_name(file_path, knowledge_id)
            oss_client.upload_local_file(object_name, file_path)
        else:
            object_name = None
        await KnowledgeFileService.create_knowledge_file(file_path, knowledge_id, login_user.user_id, object_name)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))

@router.get('/knowledge_file/select', response_model=UnifiedResponseModel)
async def select_knowledge_file(knowledge_id: str = Body(...),
                           login_user: UserPayload = Depends(get_login_user)):
    try:
        results = await KnowledgeFileService.get_knowledge_file(knowledge_id)
        knowledge_file_data = []
        for result in results:
            knowledge_file_data.append({
                'id': result.id,
                'file_name': result.file_name,
                'knowledge_id': result.knowledge_id,
                'user_id': result.user_id,
                'oss_url': result.oss_url,
                'update_time': result.update_time
            })
        return resp_200(data=knowledge_file_data)
    except Exception as err:
        return resp_500(message=str(err))

@router.delete('/knowledge_file/delete', response_model=UnifiedResponseModel)
async def delete_knowledge_file(knowledge_file_id: str = Body(...),
                                login_user: UserPayload = Depends(get_login_user)):
    try:
        await KnowledgeFileService.delete_knowledge_file(knowledge_file_id)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))
