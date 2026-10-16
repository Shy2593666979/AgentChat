from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

import pytz
from sqlalchemy import Column, DateTime, Text, text
from sqlmodel import Field, SQLModel

from agentchat.database.models.base import SQLModelSerializable


# 每个对话
class ConversationTable(SQLModelSerializable, table=True):
    __tablename__ = "conversation"

    conversation_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(description='会话话题标题，根据第一条用户消息生成')
    agent_id: str = Field(description='会话当前选择的智能体 ID，可在会话中切换')
    agent_type: str = Field(default="Agent", description="对话Conversation绑定Agent, MCPAgent or Agent")
    user_id: str = Field(description='对话Conversation的用户ID')
    summary: Optional[str] = Field(sa_column=Column(Text, nullable=True), description="对话的总结，当对话token超过一定长度时，会将较早的对话总结")
    summary_last_time: datetime = Field(
        default=datetime(1970, 1, 1),
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default="1970-01-01 00:00:00"
        ),
        description="总结上下文的最后时间"
    )
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
