from urllib.parse import urljoin
from fastapi import APIRouter, Body, UploadFile, File, Depends

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.settings import app_settings
from agentchat.utils.file_utils import get_aliyun_oss_base_path

router = APIRouter(tags=["Upload"])

@router.post("/upload", description="上传文件的接口", response_model=UnifiedResponseModel)
async def upload_file(*,
                      file: UploadFile = File(description="支持常见的Pdf、Docx、Txt、Jpg等文件"),
                      login_user: UserPayload = Depends(get_login_user)):
    try:
        file_content = await file.read()

        oss_object_name = get_aliyun_oss_base_path(file.filename)
        sign_url = urljoin(app_settings.aliyun_oss["base_url"], oss_object_name)

        aliyun_oss.sign_url_for_get(sign_url)
        aliyun_oss.upload_file(oss_object_name, file_content)

        return resp_200(sign_url)
    except Exception as err:
        return resp_500(message=str(err))