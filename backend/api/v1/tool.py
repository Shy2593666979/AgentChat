from typing import Optional

from fastapi import APIRouter, Depends, Body

from schema.schemas import UnifiedResponseModel
from api.services.user import get_login_user, UserPayload
from api.services.tool import ToolService


router = APIRouter()

@router.post('/tool/create', response_model=UnifiedResponseModel)
def create_tool(login_user: UserPayload = Depends(get_login_user),
                zh_name: str = Body(description='工具的中文名称'),
                en_name: str = Body(description='工具的英文名称'),
                description: str = Body(description='工具的描述')):

    return ToolService.create_tool(user_id=login_user.user_id, zh_name=zh_name,
                                   en_name=en_name, description=description)

@router.get('/tool/all', response_model=UnifiedResponseModel)
def get_tool(login_user: UserPayload = Depends(get_login_user)):
    return ToolService.get_all_tools()


@router.post('/tool/own', response_model=UnifiedResponseModel)
def get_personal_tool(login_user: UserPayload = Depends(get_login_user)):
    return ToolService.get_personal_tool_by_user(user_id=login_user.user_id)


@router.post('/tool/visible', response_model=UnifiedResponseModel)
def get_visible_tool(login_user: UserPayload = Depends(get_login_user)):

    return ToolService.get_visible_tool_by_user(user_id=login_user.user_id)


@router.delete('/tool/delete', response_model=UnifiedResponseModel)
def delete_tool(tool_id: str = Body(embed=True, description='工具的ID'),
                login_user: UserPayload = Depends(get_login_user)):

    return ToolService.delete_tool(tool_id=tool_id, user_id=login_user.user_id)


@router.put('/tool/update', response_model=UnifiedResponseModel)
def update_tool(tool_id: str = Body(description='工具的ID'),
                zh_name: Optional[str] = Body(description='工具的中文名称'),
                en_name: Optional[str] = Body(description='工具的英文名称'),
                description: Optional[str] = Body(description='工具的描述'),
                login_user: UserPayload = Depends(get_login_user)):

    return ToolService.update_tool(tool_id=tool_id, user_id=login_user.user_id,
                                   en_name=en_name, zh_name=zh_name, description=description)
