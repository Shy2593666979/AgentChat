from urllib.parse import urlparse
from fastapi import FastAPI, APIRouter, Body, Depends

from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.api.services.knowledge_file import KnowledgeFileService
from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.utils.file_utils import get_save_tempfile

router = APIRouter()


@router.post('/knowledge_file/create', response_model=UnifiedResponseModel)
async def upload_file(knowledge_id: str = Body(..., description="知识库的ID"),
                      file_url: str = Body(..., description="文件上传后返回的URL"),
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        # 获取本地临时文件路径
        file_name = file_url.split("/")[-1]
        local_file_path = get_save_tempfile(file_name)
        # 根据URL解析出对应的object name
        parsed = urlparse(file_url)
        object_key = parsed.path.lstrip('/')
        aliyun_oss.download_file(object_key, local_file_path)

        await KnowledgeFileService.create_knowledge_file(local_file_path, knowledge_id, login_user.user_id, file_url)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))


@router.get('/knowledge_file/select', response_model=UnifiedResponseModel)
async def select_knowledge_file(knowledge_id: str = Body(..., embed=True),
                                login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await KnowledgeService.verify_user_permission(knowledge_id, login_user.user_id)

        results = await KnowledgeFileService.get_knowledge_file(knowledge_id)
        return resp_200(data=results)
    except Exception as err:
        return resp_500(message=str(err))


@router.delete('/knowledge_file/delete', response_model=UnifiedResponseModel)
async def delete_knowledge_file(knowledge_file_id: str = Body(..., embed=True),
                                login_user: UserPayload = Depends(get_login_user)):
    try:
        # 验证用户权限
        await KnowledgeFileService.verify_user_permission(knowledge_file_id, login_user.user_id)

        await KnowledgeFileService.delete_knowledge_file(knowledge_file_id)
        return resp_200()
    except Exception as err:
        return resp_500(message=str(err))
