from typing import Optional

from fastapi import APIRouter, Depends, Body
from scipy.ndimage import uniform_filter

from service.user import get_login_user, UserPayload
from service.llm import LLMService
from type.schemas import UnifiedResponseModel

router = APIRouter()

@router.post('/llm/create', response_model=UnifiedResponseModel)
async def create_llm(model: str = Body(description='大模型的名称'),
               api_key: str = Body(description='大模型的key'),
               base_url: str = Body(description='大模型的url'),
               provider: str = Body(description='大模型的提供商'),
               login_user: UserPayload = Depends(get_login_user)):

    return LLMService.create_llm(model=model, api_key=api_key, base_url=base_url,
                                 user_id=login_user.user_id, provider=provider)

@router.delete('/llm/delete', response_model=UnifiedResponseModel)
async def delete_llm(llm_id: str = Body(description='大模型的ID'),
               login_user: UserPayload = Depends(get_login_user)):

    return LLMService.delete_llm(llm_id=llm_id, user_id=login_user.user_id)

@router.put('/llm/update', response_model=UnifiedResponseModel)
async def update_llm(model: Optional[str] = Body(description='大模型的名称'),
                     api_key: Optional[str] = Body(description='大模型的key'),
                     base_url: Optional[str] = Body(description='大模型的url'),
                     provider: Optional[str] = Body(description='大模型的提供商'),
                     llm_id: str = Body(description='大模型的ID'),
                     login_user: UserPayload = Depends(get_login_user)):

    return LLMService.update_llm(user_id=login_user.user_id, model=model, api_key=api_key,
                                 llm_id=llm_id, provider=provider, base_url=base_url)

@router.get('/llm/all', response_model=UnifiedResponseModel)
async def get_all_llm(login_user: UserPayload = Depends(get_login_user)):
    return LLMService.get_all_llm()

@router.post('/llm/personal', response_model=UnifiedResponseModel)
async def get_personal_llm(login_user: UserPayload = Depends(get_login_user)):
    return LLMService.get_personal_llm(user_id=login_user.user_id)

@router.post('/llm/visible', response_model=UnifiedResponseModel)
async def get_visible_llm(login_user: UserPayload = Depends(get_login_user)):
    return LLMService.get_visible_llm(user_id=login_user.user_id)

