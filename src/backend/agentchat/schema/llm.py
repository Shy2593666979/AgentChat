from pydantic import BaseModel

class LLMCreateReq(BaseModel):
    """
    创建大模型的请求参数模型
    """
    model: str
    api_key: str
    base_url: str
    llm_type: str = "LLM"
    provider: str = "OpenAI"


class LLMUpdateReq(BaseModel):
    """
    创建大模型的请求参数模型
    """
    llm_id: str
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