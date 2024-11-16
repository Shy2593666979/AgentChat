from sqlmodel import Field, SQLModel
from typing import Literal
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Text, Column
import pytz

# 每个Agent
class AgentTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    description: str
    logo: str
    isCustom: bool = Field(default=True)
    parameter: str = Field(sa_column=Column(Text))
    type: str = Literal["openai", "qwen"]
    code: str = Field(default="")
    createTime: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
