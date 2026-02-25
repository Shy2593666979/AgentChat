from pydantic import BaseModel, Field


class ToolCreateReq(BaseModel):
    display_name: str
    description: str
    logo_url: str
    auth_config: dict = None
    openapi_schema: dict = None

class ToolUpdateReq(BaseModel):
    tool_id: str
    description: str = None
    logo_url: str = None
    auth_config: dict = None
    display_name: str = None
    openapi_schema: dict = None

class ToolDeleteReq(BaseModel):
    tool_id: str
