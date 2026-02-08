from typing import Optional, Dict, Any
from pydantic import BaseModel

from agentchat.settings import app_settings


class MCPCreateReq(BaseModel):
    server_name: str
    url: str
    type: str
    config: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = app_settings.default_config.get("default_mcp_logo_url")


class MCPUpdateReq(BaseModel):
    server_id: str
    server_name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None


class MCPDeleteReq(BaseModel):
    server_id: str


class MCPToolsReq(BaseModel):
    server_id: str
