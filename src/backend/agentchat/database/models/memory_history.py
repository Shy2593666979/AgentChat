from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Text, Column, DateTime, text, Boolean

from agentchat.database.models.base import SQLModelSerializable


class MemoryHistoryTable(SQLModelSerializable, table=True):
    __tablename__ = "memory_history"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, description="主键ID")
    memory_id: str = Field(description="记忆ID")
    old_memory: Optional[str] = Field(default=None, sa_column=Column(Text), description="旧记忆内容")
    new_memory: Optional[str] = Field(default=None, sa_column=Column(Text), description="新记忆内容")
    event: str = Field(description="事件类型")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        ),
        description="更新时间"
    )
    is_deleted: bool = Field(default=False, sa_column=Column(Boolean), description="是否删除")
    actor_id: Optional[str] = Field(default=None, description="操作者ID")
    role: Optional[str] = Field(default=None, description="角色")

