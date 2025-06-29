from typing import Optional
from pydantic import BaseModel, Field


class ToolCreateRequest(BaseModel):
    zh_name: str = Field(description='工具的中文名称', min_length=2, max_length=10)
    en_name: str = Field(description='工具的英文名称', min_length=2, max_length=10)
    description: str = Field(description='工具的描述', max_length=300)
    logo_url: str = Field(description='用户上传的URL')

class ToolUpdateRequest(BaseModel):
    tool_id: str = Field(description='工具的ID')
    zh_name: Optional[str] = Field(default=None, description='工具的中文名称', min_length=2, max_length=10)
    en_name: Optional[str] = Field(default=None, description='工具的英文名称', min_length=2, max_length=10)
    description: Optional[str] = Field(default=None, description='工具的描述', max_length=300)
    logo_url: Optional[str] = Field(default=None, description='用户上传的URL')