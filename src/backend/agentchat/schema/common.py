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


class ModelConfig(BaseModel):
    model_name: str = ""
    api_key: str = ""
    base_url: str = ""

class MultiModels(BaseModel):
    class Config:
        # 允许从dict额外属性创建模型
        extra = "allow"

    reasoning_model: ModelConfig = Field(default_factory=ModelConfig)
    conversation_model: ModelConfig = Field(default_factory=ModelConfig)
    tool_call_model: ModelConfig = Field(default_factory=ModelConfig)
    qwen3_coder: ModelConfig = Field(default_factory=ModelConfig)
    qwen_vl: ModelConfig = Field(default_factory=ModelConfig)
    text2image: ModelConfig = Field(default_factory=ModelConfig)
    embedding: ModelConfig = Field(default_factory=ModelConfig)
    rerank: ModelConfig = Field(default_factory=ModelConfig)

class Tools(BaseModel):
    class Config:
        extra = "allow"

    weather: dict = Field(default_factory=dict)
    tavily: dict = Field(default_factory=dict)
    google: dict = Field(default_factory=dict)
    delivery: dict = Field(default_factory=dict)
    bocha: dict = Field(default_factory=dict)


class Rag(BaseModel):
    class Config:
        extra = "allow"

    enable_elasticsearch: bool = Field(default=False)
    enable_summary: bool = Field(default=False)
    retrival: dict = Field(default_factory=dict)
    split: dict = Field(default_factory=dict)
    elasticsearch: dict = Field(default_factory=dict)
    vector_db: dict = Field(default_factory=dict)