from typing import Optional

from pydantic import BaseModel, Field


class LLMCreateReq(BaseModel):
    """
    创建大模型的请求参数模型
    """
    model: str
    show_model: str = Field(default="", max_length=128, description="模型展示名称")
    api_key: str
    base_url: str
    llm_type: str = "LLM"
    provider: str = "OpenAI"


class LLMUpdateReq(BaseModel):
    """
    创建大模型的请求参数模型
    """
    llm_id: str
    show_model: Optional[str] = Field(default=None, max_length=128, description="模型展示名称，空字符串表示恢复调用标识")
    model: str = None
    api_key: str = None
    base_url: str = None
    llm_type: str = None
    provider: str = None

class LLMDeleteReq(BaseModel):
    """
    删除模型的参数类型
    """
    llm_id: str

class LLMSearchReq(BaseModel):
    """
    搜索模型的名称
    """
    llm_name: str