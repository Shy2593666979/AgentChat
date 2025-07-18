from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import uuid4
import pytz
from typing import Literal, Optional

from agentchat.database.models.base import SQLModelSerializable


# 每个对话
class DialogTable(SQLModelSerializable, table=True):
    __tablename__ = "dialog"

    dialog_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(description='对话绑定的Agent的名称')
    agent_id: str = Field(description='对话Dialog绑定Agent的ID')
    agent_type: str = Field(default="Agent", description="对话Dialog绑定Agent, MCPAgent or Agent")
    user_id: str = Field(description='对话Dialog的用户ID')
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
