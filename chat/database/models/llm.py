from sqlmodel import SQLModel
from pydantic import Field

class LLMTable(SQLModel, table=True):
    llm_id: str = Field(description='大模型的ID')
    model: str = Field(description='大模型的名称')
    base_url: str = Field(description='大模型的base url')
    api_key: str = Field(description='大模型的api key')
    provider: str = Field(description='模型的提供商')


