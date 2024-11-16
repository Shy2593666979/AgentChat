from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Text, Column
import pytz

# 拉踩的信息
class MessageDownTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    userInput: str = Field(sa_column=Column(Text))
    agentOutput: str = Field(sa_column=Column(Text))
    createTime: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

# 点赞的信息
class MessageLikeTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    userInput: str = Field(sa_column=Column(Text))
    agentOutput: str = Field(sa_column=Column(Text))
    createTime: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))