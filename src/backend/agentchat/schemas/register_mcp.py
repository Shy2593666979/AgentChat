from typing import Optional, Any, Literal, List, Dict
from pydantic import BaseModel, Field, field_validator


class RegisterMcpRequest(BaseModel):
    """
    通过 OpenAPI 3.1+ schemas 注册 MCP 服务。

    - `mcp_id`         可选，不传则自动生成 UUID
    - `name`           必传，则从 openapi_schema.info.title 推断
    - `description`    可选，服务描述，不传则从 openapi_schema.info.description 推断
    - `openapi_schema` 必传，标准 OpenAPI 3.1+ 文档对象
    """
    mcp_id: Optional[str] = None
    name: str
    transport: Literal["sse", "streamable_http"] = "sse"
    description: Optional[str] = None
    openapi_schema: dict[str, Any]


class RegisterMcpResponse(BaseModel):
    mcp_id: str
    remote_url: str
    name: str
    tool_count: int

class DeleteMcpTaskRequest(BaseModel):
    task_id: str

class RegisterMcpToolParameterProperty(BaseModel):
    type: str  # "string", "number", "boolean", "array", "object"
    description: str = ""
    x_position: str = Field(alias="x-position")  # "path", "query", "header", "cookie", "body"
    default: Optional[Any] = None
    items: Optional[dict] = None  # 用于 array 类型


class RegisterMcpToolParameter(BaseModel):
    type: str = "object"
    properties: Dict[str, RegisterMcpToolParameterProperty]
    required: List[str] = []
    additionalProperties: bool = False

class RegisterMcpToolApiInfo(BaseModel):
    base_url: str
    path: str
    method: str
    content_type: str

class RegisterMcpToolModel(BaseModel):
    name: str
    description: str = ""
    parameters: RegisterMcpToolParameter
    api_info: RegisterMcpToolApiInfo

class RegisterMcpServerModel(BaseModel):
    name: str
    transport: Literal["sse", "streamable_http"] = "sse"
    description: str = ""
    tools: List[RegisterMcpToolModel] = Field(..., min_length=1)







