from sqlmodel import Field, SQLModel
from typing import Literal, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Text, Column
import pytz

# 每个Agent
class AgentTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(default='')
    description: str = Field(default='')
    logo: str = Field(default='img/default.png')
    user_id: Optional[int] = Field(index=True)
    is_custom: bool = Field(default=True)
    llm_id: str = Field(description='Agent绑定的模型')
    tool_id: List[str] = Field(default=[], description='Agent绑定的工具列表')
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
