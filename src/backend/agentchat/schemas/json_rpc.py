from typing import Optional, Any
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    server_name: str
    active_sessions: int
    timestamp: int


class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[str] = None


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None