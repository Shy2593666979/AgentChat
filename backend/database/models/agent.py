from sqlmodel import Field, SQLModel
from typing import Literal, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, Column
import pytz

# 每个Agent
class AgentTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(default='')
    description: str = Field(default='')
    logo: str = Field(default='img/agent/agent.png')
    user_id: Optional[str] = Field(index=True)
    is_custom: bool = Field(default=True)
    llm_id: str = Field(default=None, description='Agent绑定的LLM模型')
    embedding_id: str = Field(default=None, description='Agent绑定的Embedding模型')
    tool_id: List[str] = Field(default=[], sa_column=Column(JSON),description='Agent绑定的工具列表')
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
