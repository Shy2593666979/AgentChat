from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4
import pytz

class LLMTable(SQLModel, table=True):
    llm_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    llm_type: str = Field(default='LLM', description='大模型的类型, 分LLM、Embedding、Rerank')
    model: str = Field(description='大模型的名称')
    base_url: str = Field(description='大模型的base url')
    api_key: str = Field(description='大模型的api key')
    provider: str = Field(description='大模型的提供商')
    user_id: str = Field(description='大模型创建者的ID')
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))


