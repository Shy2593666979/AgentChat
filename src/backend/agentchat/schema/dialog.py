from pydantic import BaseModel, Field
from typing import Optional


class DialogCreateRequest(BaseModel):
    name: str = Field(description='对话Agent名称')
    agent_id: str = Field(description='对话Agent的ID')
    agent_type: str = Field("Agent", description="Agent的类型，仅支持MCPAgent or Agent")


class DialogUpdateRequest(BaseModel):
    name: Optional[str] = Field(description='对话Agent名称')
    agent_id: Optional[str] = Field(description='对话Agent的ID')
    dialog_id: str = Field(description='对话的ID')
    agent_type: Optional[str] = Field("Agent", description="Agent的类型，仅支持MCPAgent or Agent")

