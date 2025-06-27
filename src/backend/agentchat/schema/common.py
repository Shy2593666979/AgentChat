from typing import List, Optional
from pydantic import BaseModel, Field


class CreateLLMRequest(BaseModel):
    """
    创建大模型的请求参数模型
    """
    model: str = Field(..., description="大模型的名称")
    api_key: str = Field(..., description="大模型的 API Key")
    base_url: str = Field(..., description="大模型服务的基础 URL")
    llm_type: str = Field(..., description="模型类型，例如 LLM、Embedding")
    provider: str = Field(..., description="大模型提供商，例如 OpenAI、Anthropic")


class UpdateLLMRequest(BaseModel):
    """
    创建大模型的请求参数模型
    """
    model: str = Field(None, description="大模型的名称")
    api_key: str = Field(None, description="大模型的 API Key")
    base_url: str = Field(None, description="大模型服务的基础 URL")
    llm_type: str = Field(None, description="模型类型，例如 LLM、Embedding")
    llm_id: str = Field(..., description="大模型的ID")
    provider: str = Field(None, description="大模型提供商，例如 OpenAI、Anthropic")

