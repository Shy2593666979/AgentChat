from typing import Optional, Dict
from pydantic import BaseModel

class MCPUserConfigCreateRequest(BaseModel):
    mcp_server_id: str
    config: Optional[Dict] = None

class MCPUserConfigUpdateRequest(BaseModel):
    config_id: str
    mcp_server_id: str
    config: Optional[Dict] = None