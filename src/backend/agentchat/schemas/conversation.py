from typing import Optional

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    name: str = Field("新会话", description='会话初始标题，首条消息后异步生成话题标题')
    agent_id: str = Field(description='对话Agent的ID')
    agent_type: str = Field("Agent", description="Agent的类型，仅支持MCPAgent or Agent")


class ConversationUpdateRequest(BaseModel):
    name: Optional[str] = Field(description='对话Agent名称')
    agent_id: Optional[str] = Field(description='对话Agent的ID')
    conversation_id: str = Field(description='对话的ID')
    agent_type: Optional[str] = Field("Agent", description="Agent的类型，仅支持MCPAgent or Agent")


class ConversationAgentUpdateRequest(BaseModel):
    conversation_id: str = Field(min_length=1, description="要切换智能体的会话 ID")
    agent_id: str = Field(min_length=1, description="要使用的智能体 ID")
