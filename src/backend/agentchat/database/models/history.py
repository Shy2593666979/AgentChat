from datetime import datetime
from typing import List, Literal, Optional
from uuid import uuid4

import pytz
from sqlalchemy import JSON, Column, DateTime, Text, text
from sqlmodel import Field, SQLModel

from agentchat.database.models.base import SQLModelSerializable


# 每条消息
class HistoryTable(SQLModelSerializable, table=True):
    __tablename__ = "history"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    conversation_id: str = Field(description="对话的ID")
    role: str = Literal["assistant", "system", "user"]
    token_usage: int = Field(0, description="当前消息Token 的使用量")
    events: List[dict] = Field(default=[], sa_column=Column(JSON), description="AI回复事件信息 {'type': 'event', 'data': ....}")
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

