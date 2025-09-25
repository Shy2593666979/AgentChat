from typing import List, Optional
from pydantic import BaseModel, Field

class CreateAgentRequest(BaseModel):
    name: str = Field(..., description="Agent 名称")
    description: str = Field(..., description="Agent 描述")
    tool_ids: List[str] = Field(default=[], description="绑定的工具ID")
    llm_id: Optional[str] = Field(None, description="Agent 绑定的LLM ID")
    mcp_ids: List[str] = Field(default=[], description="绑定的MCP Server")
    knowledge_ids: List[str] = Field(default=[], description="绑定的知识库ID")
    enable_memory: bool = Field(True, description="是否使用嵌入")
    system_prompt: str = Field(..., description="Agent 系统提示词")
    logo_url: str = Field(..., description="Logo URL")


class UpdateAgentRequest(BaseModel):
    agent_id: str = Field(..., description="要更新的 Agent ID")
    name: Optional[str] = Field(None, description="Agent 名称")
    description: Optional[str] = Field(None, description="Agent 描述")
    tool_ids: Optional[List[str]] = Field(None, description="绑定的工具ID")
    knowledge_ids: Optional[List[str]] = Field(None, description="绑定的知识库ID")
    mcp_ids: Optional[List[str]] = Field(None, description="绑定的MCP Server")
    llm_id: Optional[str] = Field(None, description="Agent 绑定的LLM ID")
    enable_memory: Optional[bool] = Field(True, description="是否使用嵌入")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    system_prompt: str = Field(None, description="Agent 系统提示词")