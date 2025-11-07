from typing import Optional

from sqlalchemy import DateTime, text, Column
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4

from agentchat.database.models.base import SQLModelSerializable


class LLMTable(SQLModelSerializable, table=True):
    __tablename__ = "llm"

    llm_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    llm_type: str = Field(default='LLM', description='大模型的类型, 分LLM、Embedding、Rerank')
    model: str = Field(description='大模型的名称')
    base_url: str = Field(description='大模型的base url')
    api_key: str = Field(description='大模型的api key')
    provider: str = Field(description='大模型的提供商')
    user_id: str = Field(description='大模型创建者的ID')
    update_time: Optional[datetime] = Field(sa_column=Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP')
    ),
        description="修改时间"
    )
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )


