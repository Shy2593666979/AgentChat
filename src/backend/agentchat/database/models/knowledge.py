import pytz
from sqlmodel import Field, SQLModel
from typing import Literal, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, Column, DateTime, text

from agentchat.database.models.base import SQLModelSerializable

# 规范Milvus 和 Elasticsearch的命名名称
def get_knowledge_id():
    return f"t_{uuid4().hex[:16]}"  # 缩短 ID 长度

class KnowledgeTable(SQLModelSerializable, table=True):
    __tablename__ = "knowledge"

    id: str = Field(default_factory=get_knowledge_id, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=128)
    description: Optional[str] = Field(max_length=1024, default=None)
    user_id: Optional[str] = Field(index=True, max_length=128, default=None)
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
