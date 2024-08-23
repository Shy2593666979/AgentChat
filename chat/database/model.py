from sqlmodel import Field, SQLModel, create_engine, Session
from typing import Literal
from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy import Text, Column

# 每个函数 or 工具
class AgentTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    description: str
    logo: str
    isCustom: bool = Field(default=True)
    parameter: str = Field(sa_column=Column(Text))
    type: str = Literal["openai", "qwen"]
    code: str = Field(default="")
    createTime: datetime = Field(default_factory=datetime.utcnow)

# 每条消息
class HistoryTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    dialogId: str
    role: str = Literal["assistant", "system", "user"]
    createTime: datetime = Field(default_factory=datetime.utcnow)

# 每个对话
class DialogTable(SQLModel, table=True):
    dialogId: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    agent: str
    createTime: datetime = Field(default_factory=datetime.utcnow)

# 拉踩的信息
class MessageDownTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    userInput: str = Field(sa_column=Column(Text))
    agentOutput: str = Field(sa_column=Column(Text))
    createTime: datetime = Field(default_factory=datetime.utcnow)

# 点赞的信息
class MessageLikeTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    userInput: str = Field(sa_column=Column(Text))
    agentOutput: str = Field(sa_column=Column(Text))
    createTime: datetime = Field(default_factory=datetime.utcnow)