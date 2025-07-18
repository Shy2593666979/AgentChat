from typing import Optional

from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Text, Column, DateTime, text
import pytz

from agentchat.database.models.base import SQLModelSerializable


# 拉踩的信息
class MessageDownTable(SQLModelSerializable, table=True):
    __tablename__ = "message_down"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_input: str = Field(sa_column=Column(Text))
    agent_output: str = Field(sa_column=Column(Text))
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

# 点赞的信息
class MessageLikeTable(SQLModelSerializable, table=True):
    __tablename__ = "message_like"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_input: str = Field(sa_column=Column(Text))
    agent_output: str = Field(sa_column=Column(Text))
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