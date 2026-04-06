from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class OpenApiContact(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None

class OpenApiLicense(BaseModel):
    name: str
    identifier: Optional[str] = None
    url: Optional[str] = None

class OpenApiInfo(BaseModel):
    title: str
    version: str
    description: Optional[str] = None
    summary: Optional[str] = None
    contact: Optional[OpenApiContact] = None
    license: Optional[OpenApiLicense] = None

class OpenApiServer(BaseModel):
    url: str
    description: Optional[str] = None

class OpenApiSchema(BaseModel):
    openapi: str = Field(..., pattern=r"^3\.1\.\d+$", description="必须是 OpenAPI 3.1.x 版本")
    info: OpenApiInfo
    jsonSchemaDialect: Optional[str] = None # OpenAPI 3.1 新增字段
    servers: Optional[List[OpenApiServer]] = None
    paths: Optional[Dict[str, Any]] = None
    webhooks: Optional[Dict[str, Any]] = None # OpenAPI 3.1 新增字段
    components: Optional[Dict[str, Any]] = None