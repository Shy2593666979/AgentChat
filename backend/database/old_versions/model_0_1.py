# -------------------------------
# 该文件目前版本已弃用
# -------------------------------

from sqlmodel import Field, SQLModel, create_engine, Session
from typing import Literal
from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy import Text, Column
import pytz

# 每个Agent
class AgentTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    description: str
    logo: str
    is_custom: bool = Field(default=True)
    parameter: str = Field(sa_column=Column(Text))
    type: str = Literal["openai", "qwen"]
    code: str = Field(default="")
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

# 每条消息
class HistoryTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    dialog_id: str
    role: str = Literal["assistant", "system", "user"]
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

# 每个对话
class DialogTable(SQLModel, table=True):
    dialog_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    agent: str
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

# 拉踩的信息
class MessageDownTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_input: str = Field(sa_column=Column(Text))
    agent_output: str = Field(sa_column=Column(Text))
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

# 点赞的信息
class MessageLikeTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_input: str = Field(sa_column=Column(Text))
    agent_output: str = Field(sa_column=Column(Text))
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))